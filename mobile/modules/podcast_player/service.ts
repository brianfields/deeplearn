/**
 * Podcast Player Service
 *
 * Handles audio playback orchestration, persistence, and playback controls.
 * Uses expo-audio for cross-platform audio support.
 */

import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import type { AudioPlayer } from 'expo-audio';
import type { PersistedUnitState, PlaybackSpeed, PodcastTrack } from './models';
import {
  PLAYBACK_SPEEDS,
  getPodcastStoreState,
  usePodcastStore,
} from './store';
import { PodcastPlayerRepo } from './repo';

function isValidSpeed(speed: number): speed is PlaybackSpeed {
  return (PLAYBACK_SPEEDS as readonly number[]).includes(speed);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export class PodcastPlayerService {
  private isInitialized = false;
  private initializationPromise: Promise<void> | null = null;
  private currentTrackId: string | null = null;
  private player: AudioPlayer | null = null;
  private statusUpdateInterval: ReturnType<typeof setInterval> | null = null;
  private isPlayPending = false; // Flag to prevent status polling from overriding play() calls
  private repo: PodcastPlayerRepo;

  constructor(repo: PodcastPlayerRepo = new PodcastPlayerRepo()) {
    this.repo = repo;
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = (async () => {
      await setAudioModeAsync({
        playsInSilentMode: true,
        shouldPlayInBackground: true,
        interruptionMode: 'duckOthers',
        interruptionModeAndroid: 'duckOthers',
      });
      await this.hydrateGlobalSpeed();
      this.isInitialized = true;
    })();

    try {
      await this.initializationPromise;
    } finally {
      this.initializationPromise = null;
    }
  }

  async loadTrack(track: PodcastTrack): Promise<void> {
    await this.initialize();
    const store = getPodcastStoreState();
    const { currentTrack, playbackState } = store;

    store.updatePlaybackState({ isLoading: true });

    if (this.currentTrackId && this.currentTrackId !== track.unitId) {
      await this.savePosition(this.currentTrackId, playbackState.position);
    }

    const isSameTrack = currentTrack?.unitId === track.unitId;
    if (!isSameTrack) {
      // Stop and release previous player
      if (this.player) {
        this.player.pause();
        this.player.remove();
        this.player = null;
      }
      // Clear status update interval
      if (this.statusUpdateInterval) {
        clearInterval(this.statusUpdateInterval);
        this.statusUpdateInterval = null;
      }
      this.currentTrackId = track.unitId;
      store.setCurrentTrack(track);
      store.updatePlaybackState({
        position: 0,
        duration: track.durationSeconds,
        isPlaying: false,
      });
    }

    // Create new player if needed
    if (!this.player) {
      console.log(
        '[PodcastPlayer] Creating new audio player for:',
        track.title
      );
      this.player = createAudioPlayer({ uri: track.audioUrl });

      // Set up status polling
      this.statusUpdateInterval = setInterval(() => {
        this.updatePlaybackStatus();
      }, 500);
      console.log('[PodcastPlayer] Player created successfully');
    } else {
      console.log('[PodcastPlayer] Reusing existing player for:', track.title);
    }

    const persistedState = await this.getPersistedUnitState(track.unitId);
    const startPosition = clamp(
      persistedState?.position ?? 0,
      0,
      track.durationSeconds || Number.MAX_SAFE_INTEGER
    );

    if (startPosition > 0) {
      await this.player.seekTo(startPosition);
    }

    const speed = store.globalSpeed;
    this.player.setPlaybackRate(speed);

    store.setCurrentTrack(track);
    store.updatePlaybackState({
      position: startPosition,
      duration: track.durationSeconds,
      isPlaying: false,
      isLoading: false,
    });
  }

  async play(): Promise<void> {
    console.log('[PodcastPlayer] play() called');
    await this.initialize();
    if (!this.player) {
      console.warn('[PodcastPlayer] Cannot play: no player instance');
      return;
    }
    try {
      const currentTime = this.player.currentTime ?? 0;
      const duration = this.player.duration ?? 0;

      console.log(
        '[PodcastPlayer] Current position:',
        currentTime,
        'Duration:',
        duration
      );

      // If we're at or very close to the end, restart from beginning
      if (duration > 0 && currentTime >= duration - 1) {
        console.log('[PodcastPlayer] At end of track, seeking to beginning');
        await this.player.seekTo(0);
      }

      console.log('[PodcastPlayer] Calling player.play()');
      this.isPlayPending = true; // Prevent status polling from overriding
      this.player.play();
      console.log(
        '[PodcastPlayer] After play() - player.playing:',
        this.player.playing
      );

      usePodcastStore.getState().updatePlaybackState({
        isPlaying: true,
        isLoading: false,
      });
      console.log('[PodcastPlayer] State updated to isPlaying: true');

      // Give the player time to start, then clear the pending flag
      setTimeout(() => {
        this.isPlayPending = false;
        console.log('[PodcastPlayer] Cleared play pending flag');
      }, 1000); // Give it a full second to start
    } catch (error) {
      console.error('[PodcastPlayer] Play failed:', error);
      this.isPlayPending = false; // Clear the flag on error
      usePodcastStore.getState().updatePlaybackState({
        isPlaying: false,
        isLoading: false,
      });
    }
  }

  async pause(): Promise<void> {
    await this.initialize();
    if (this.player) {
      this.player.pause();
    }
    usePodcastStore.getState().updatePlaybackState({
      isPlaying: false,
    });
  }

  async pauseCurrentTrack(): Promise<void> {
    const store = getPodcastStoreState();
    if (!store.currentTrack) {
      return;
    }
    await this.pause();
  }

  async skipForward(seconds: number): Promise<void> {
    const store = getPodcastStoreState();
    const { playbackState } = store;
    const duration = playbackState.duration || Number.MAX_SAFE_INTEGER;
    const nextPosition = clamp(playbackState.position + seconds, 0, duration);
    await this.seekTo(nextPosition);
  }

  async skipBackward(seconds: number): Promise<void> {
    const store = getPodcastStoreState();
    const { playbackState } = store;
    const nextPosition = clamp(
      playbackState.position - seconds,
      0,
      playbackState.duration || Number.MAX_SAFE_INTEGER
    );
    await this.seekTo(nextPosition);
  }

  async seekTo(position: number): Promise<void> {
    await this.initialize();
    const store = getPodcastStoreState();
    const duration = store.playbackState.duration || Number.MAX_SAFE_INTEGER;
    const clamped = clamp(position, 0, duration);
    if (this.player) {
      await this.player.seekTo(clamped);
    }
    store.updatePlaybackState({ position: clamped });
    const trackId = store.currentTrack?.unitId;
    if (trackId) {
      await this.savePosition(trackId, clamped);
    }
  }

  async setSpeed(speed: PlaybackSpeed): Promise<void> {
    await this.initialize();
    usePodcastStore.getState().setGlobalSpeed(speed);
    if (this.player) {
      this.player.setPlaybackRate(speed);
    }
    await this.repo.saveGlobalSpeed(speed);
  }

  getSpeed(): PlaybackSpeed {
    return usePodcastStore.getState().globalSpeed;
  }

  async getPosition(unitId: string): Promise<number> {
    const persisted = await this.getPersistedUnitState(unitId);
    return persisted?.position ?? 0;
  }

  async savePosition(unitId: string, position: number): Promise<void> {
    if (!Number.isFinite(position)) {
      return;
    }
    await this.repo.saveUnitPosition(unitId, position);
    const store = getPodcastStoreState();
    if (store.currentTrack?.unitId === unitId) {
      store.updatePlaybackState({ position });
    }
  }

  getCurrentTrack(): PodcastTrack | null {
    return usePodcastStore.getState().currentTrack;
  }

  async hydrateGlobalSpeed(): Promise<void> {
    const speed = await this.repo.getGlobalSpeed();
    if (speed && isValidSpeed(speed)) {
      usePodcastStore.getState().setGlobalSpeed(speed);
      if (this.player) {
        this.player.setPlaybackRate(speed);
      }
    }
  }

  private updatePlaybackStatus(): void {
    if (!this.player) {
      return;
    }

    const store = usePodcastStore.getState();
    const isPlaying = this.player.playing ?? false;
    const isLoading = this.player.isBuffering ?? false;
    const position = this.player.currentTime ?? 0;
    const duration = this.player.duration ?? 0;

    // Only update if values have changed significantly (avoid unnecessary re-renders)
    const currentState = store.playbackState;

    // Don't override isPlaying to false if we just called play()
    const shouldUpdateIsPlaying = !this.isPlayPending || isPlaying;

    const hasSignificantChange =
      Math.abs(position - currentState.position) > 0.5 ||
      (shouldUpdateIsPlaying && isPlaying !== currentState.isPlaying) ||
      isLoading !== currentState.isLoading ||
      Math.abs(duration - (currentState.duration ?? 0)) > 0.5;

    if (hasSignificantChange) {
      console.log('[PodcastPlayer] Status update:', {
        isPlaying,
        position: position.toFixed(2),
        duration: duration.toFixed(2),
        isBuffering: isLoading,
        isPlayPending: this.isPlayPending,
        willUpdateIsPlaying: shouldUpdateIsPlaying,
      });

      // Build the update object, conditionally including isPlaying
      const update: any = {
        isLoading,
        position,
        duration,
      };

      if (shouldUpdateIsPlaying) {
        update.isPlaying = isPlaying;
      }

      store.updatePlaybackState(update);

      // If player actually started playing, clear the pending flag
      if (this.isPlayPending && isPlaying) {
        this.isPlayPending = false;
        console.log(
          '[PodcastPlayer] Player started, cleared play pending flag'
        );
      }
    }

    // Save position periodically (throttle to avoid excessive writes)
    const currentTrack = store.currentTrack;
    if (currentTrack && position > 0 && Math.floor(position) % 5 === 0) {
      this.savePosition(currentTrack.unitId, position).catch(() => {});
    }
  }

  private async getPersistedUnitState(
    unitId: string
  ): Promise<PersistedUnitState | null> {
    return this.repo.getUnitState(unitId);
  }
}

let serviceInstance: PodcastPlayerService | null = null;

export function getPodcastPlayerService(): PodcastPlayerService {
  if (!serviceInstance) {
    serviceInstance = new PodcastPlayerService();
  }
  return serviceInstance;
}

export function __resetPodcastPlayerServiceForTests(): void {
  serviceInstance = null;
  usePodcastStore.getState().reset();
}
