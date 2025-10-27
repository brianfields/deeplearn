/**
 * Podcast Player Service
 *
 * Handles audio playback orchestration, persistence, and playback controls.
 * Uses react-native-track-player for background capable audio playback.
 */

import TrackPlayer, {
  AppKilledPlaybackBehavior,
  Capability,
  Event,
  RepeatMode,
  State as TrackPlayerState,
} from 'react-native-track-player';
import type {
  PersistedUnitState,
  PlaybackSpeed,
  PodcastTrack,
  UnitPodcastPlaylist,
} from './models';
import {
  PLAYBACK_SPEEDS,
  getPodcastStoreState,
  usePodcastStore,
} from './store';
import { PodcastPlayerRepo } from './repo';

const DEFAULT_ARTIST = 'DeepLearn';

interface TrackPlayerEventSubscription {
  remove: () => void;
}

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
  private progressSubscription: TrackPlayerEventSubscription | null = null;
  private stateSubscription: TrackPlayerEventSubscription | null = null;
  private queueEndedSubscription: TrackPlayerEventSubscription | null = null;
  private repo: PodcastPlayerRepo;

  constructor(repo: PodcastPlayerRepo = new PodcastPlayerRepo()) {
    this.repo = repo;
  }

  private getTrackKey(track: PodcastTrack): string {
    if (track.lessonId) {
      return `${track.unitId}:lesson:${track.lessonId}`;
    }
    if (typeof track.lessonIndex === 'number') {
      return `${track.unitId}:lesson-index:${track.lessonIndex}`;
    }
    return `${track.unitId}:intro`;
  }

  private isSameTrack(a: PodcastTrack, b: PodcastTrack): boolean {
    if (a.lessonId && b.lessonId) {
      return a.lessonId === b.lessonId;
    }
    if (!a.lessonId && !b.lessonId) {
      return a.unitId === b.unitId;
    }
    return false;
  }

  private detachEventListeners(): void {
    if (this.progressSubscription) {
      this.progressSubscription.remove();
      this.progressSubscription = null;
    }
    if (this.stateSubscription) {
      this.stateSubscription.remove();
      this.stateSubscription = null;
    }
    if (this.queueEndedSubscription) {
      this.queueEndedSubscription.remove();
      this.queueEndedSubscription = null;
    }
  }

  async initialize(): Promise<void> {
    console.log('[PodcastPlayerService] 🔧 Initialize called');
    if (this.isInitialized) {
      console.log('[PodcastPlayerService] ✅ Already initialized');
      return;
    }
    if (this.initializationPromise) {
      console.log(
        '[PodcastPlayerService] ⏳ Initialization in progress, waiting...'
      );
      return this.initializationPromise;
    }

    console.log('[PodcastPlayerService] 🚀 Starting initialization...');
    this.initializationPromise = (async () => {
      try {
        console.log('[PodcastPlayerService] 📱 Setting up TrackPlayer...');
        await TrackPlayer.setupPlayer();
        console.log('[PodcastPlayerService] ⚙️ Updating player options...');
        await TrackPlayer.updateOptions({
          capabilities: [
            Capability.Play,
            Capability.Pause,
            Capability.SeekTo,
            Capability.Stop,
          ],
          compactCapabilities: [
            Capability.Play,
            Capability.Pause,
            Capability.SeekTo,
          ],
          progressUpdateEventInterval: 1,
          android: {
            appKilledPlaybackBehavior:
              AppKilledPlaybackBehavior.StopPlaybackAndRemoveNotification,
          },
        });
        console.log('[PodcastPlayerService] 🔁 Setting repeat mode...');
        await TrackPlayer.setRepeatMode(RepeatMode.Off);
        console.log('[PodcastPlayerService] 📡 Attaching event listeners...');
        this.attachEventListeners();
        console.log('[PodcastPlayerService] 💾 Hydrating global speed...');
        await this.hydrateGlobalSpeed();
        this.isInitialized = true;
        console.log('[PodcastPlayerService] ✅ Initialization complete!');
      } catch (error) {
        console.error(
          '[PodcastPlayerService] ❌ Initialization failed:',
          error
        );
        throw error;
      }
    })();

    try {
      await this.initializationPromise;
    } finally {
      this.initializationPromise = null;
    }
  }

  /**
   * Safely resets the TrackPlayer with initialization checks.
   * Ensures the player is fully ready before attempting to reset,
   * which prevents KVO observer lifecycle issues.
   */
  private async safeReset(): Promise<void> {
    // Ensure player is initialized before attempting reset
    if (!this.isInitialized) {
      console.log(
        '[PodcastPlayerService] ⚠️ Skipping reset - player not initialized'
      );
      return;
    }

    try {
      // Check that the player is in a valid state by querying its state
      await TrackPlayer.getState();
      console.log(
        '[PodcastPlayerService] ✅ Player ready, proceeding with reset'
      );
      await TrackPlayer.reset();
    } catch (error) {
      console.warn(
        '[PodcastPlayerService] ⚠️ Reset failed or player not ready:',
        error
      );
      // If getState fails, the player may not be fully set up yet
      // In this case, we skip the reset as there's nothing to clean up
    }
  }

  private attachEventListeners(): void {
    this.detachEventListeners();
    this.queueEndedSubscription = TrackPlayer.addEventListener(
      Event.PlaybackQueueEnded,
      this.handleQueueEnded
    );
  }

  private handleQueueEnded = (): void => {
    void this.advanceFromQueueEnd();
  };

  private async advanceFromQueueEnd(): Promise<void> {
    const store = getPodcastStoreState();
    const playlist = store.playlist;
    if (!playlist) {
      return;
    }

    if (!store.autoplayEnabled) {
      store.updatePlaybackState({ isPlaying: false });
      return;
    }

    const nextIndex = playlist.currentTrackIndex + 1;
    if (nextIndex >= playlist.tracks.length) {
      store.updatePlaybackState({ isPlaying: false });
      return;
    }

    await this.advanceToIndex(nextIndex, true);
  }

  private async advanceToIndex(
    index: number,
    autoplayOverride?: boolean
  ): Promise<void> {
    const store = getPodcastStoreState();
    const playlist = store.playlist;
    if (!playlist) {
      return;
    }

    const targetTrack = playlist.tracks[index];
    if (!targetTrack) {
      return;
    }

    await this.loadTrack(targetTrack);
    const shouldAutoplay =
      typeof autoplayOverride === 'boolean'
        ? autoplayOverride
        : store.autoplayEnabled;
    if (shouldAutoplay) {
      await this.play();
    }
  }

  async loadTrack(track: PodcastTrack): Promise<void> {
    console.log('[PodcastPlayerService] 🎵 loadTrack called');
    console.log('[PodcastPlayerService] Track details:', {
      unitId: track.unitId,
      title: track.title,
      audioUrl: track.audioUrl,
      durationSeconds: track.durationSeconds,
    });

    await this.initialize();
    const store = getPodcastStoreState();
    const { playbackState } = store;
    const trackKey = this.getTrackKey(track);

    console.log('[PodcastPlayerService] 📝 Setting loading state...');
    store.updatePlaybackState({ isLoading: true });

    if (this.currentTrackId && this.currentTrackId !== trackKey) {
      console.log('[PodcastPlayerService] 💾 Saving previous track position:', {
        trackId: this.currentTrackId,
        position: playbackState.position,
      });
      await this.savePosition(this.currentTrackId, playbackState.position);
    }

    console.log('[PodcastPlayerService] 🔄 Resetting TrackPlayer...');
    await this.safeReset();

    this.currentTrackId = trackKey;
    store.setCurrentTrack(track);
    const playlist = store.playlist;
    if (playlist) {
      const trackIndex = playlist.tracks.findIndex(playlistTrack =>
        this.isSameTrack(playlistTrack, track)
      );
      if (trackIndex >= 0 && playlist.currentTrackIndex !== trackIndex) {
        store.setCurrentTrackIndex(trackIndex);
      }
    }
    store.updatePlaybackState({
      position: 0,
      duration: track.durationSeconds,
      buffered: 0,
      isPlaying: false,
    });

    console.log('[PodcastPlayerService] 📖 Loading persisted state...');
    const persistedState = await this.getPersistedTrackState(trackKey);
    const startPosition = clamp(
      persistedState?.position ?? 0,
      0,
      track.durationSeconds || Number.MAX_SAFE_INTEGER
    );
    console.log('[PodcastPlayerService] Start position:', startPosition);

    console.log('[PodcastPlayerService] ➕ Adding track to player...');
    const trackToAdd = {
      id: trackKey,
      url: track.audioUrl,
      title: track.title,
      artist: DEFAULT_ARTIST,
      duration: track.durationSeconds,
    };
    console.log('[PodcastPlayerService] Track object:', trackToAdd);

    try {
      await TrackPlayer.add(trackToAdd);
      console.log('[PodcastPlayerService] ✅ Track added successfully');
    } catch (error) {
      console.error('[PodcastPlayerService] ❌ Failed to add track:', error);
      throw error;
    }

    const speed = store.globalSpeed;
    console.log('[PodcastPlayerService] ⚡ Setting playback rate:', speed);
    await TrackPlayer.setRate(speed);

    if (startPosition > 0) {
      console.log(
        '[PodcastPlayerService] ⏩ Seeking to position:',
        startPosition
      );
      await TrackPlayer.seekTo(startPosition);
    }

    console.log('[PodcastPlayerService] ✅ Updating final state...');
    store.updatePlaybackState({
      position: startPosition,
      duration: track.durationSeconds,
      buffered: 0,
      isPlaying: false,
      isLoading: false,
    });
    console.log('[PodcastPlayerService] ✅ loadTrack complete');
  }

  async loadPlaylist(unitId: string, tracks: PodcastTrack[]): Promise<void> {
    await this.initialize();
    const store = getPodcastStoreState();
    const validTracks = tracks.filter(track => !!track.audioUrl);

    if (validTracks.length === 0) {
      this.currentTrackId = null;
      store.setPlaylist(null);
      await this.safeReset();
      return;
    }

    const existingPlaylist = store.playlist;
    const currentTrack = store.currentTrack;
    let currentTrackIndex = 0;

    if (
      existingPlaylist &&
      existingPlaylist.unitId === unitId &&
      currentTrack
    ) {
      const matchedIndex = validTracks.findIndex(track =>
        this.isSameTrack(track, currentTrack)
      );
      if (matchedIndex >= 0) {
        currentTrackIndex = matchedIndex;
      }
    }

    const playlist: UnitPodcastPlaylist = {
      unitId,
      tracks: validTracks,
      currentTrackIndex,
    };

    store.setPlaylist(playlist);
  }

  async skipToNext(): Promise<void> {
    const store = getPodcastStoreState();
    const playlist = store.playlist;
    if (!playlist) {
      return;
    }

    const nextIndex = playlist.currentTrackIndex + 1;
    if (nextIndex >= playlist.tracks.length) {
      await this.seekTo(0);
      store.updatePlaybackState({ isPlaying: false });
      return;
    }

    await this.advanceToIndex(nextIndex, true);
  }

  async skipToPrevious(): Promise<void> {
    const store = getPodcastStoreState();
    const playlist = store.playlist;
    if (!playlist) {
      return;
    }

    const position = store.playbackState.position;
    if (position > 5 || playlist.currentTrackIndex === 0) {
      await this.seekTo(0);
      await this.play();
      return;
    }

    const previousIndex = playlist.currentTrackIndex - 1;
    if (previousIndex >= 0) {
      await this.advanceToIndex(previousIndex, true);
    }
  }

  async play(): Promise<void> {
    console.log('[PodcastPlayerService] ▶️ play() called');
    await this.initialize();
    if (!this.currentTrackId) {
      console.warn('[PodcastPlayerService] ⚠️ Cannot play: no active track');
      return;
    }

    console.log(
      '[PodcastPlayerService] Current track ID:',
      this.currentTrackId
    );

    try {
      console.log('[PodcastPlayerService] 📊 Getting current progress...');
      const progress = await TrackPlayer.getProgress();
      console.log('[PodcastPlayerService] Progress:', progress);

      const duration = progress.duration ?? 0;
      const position = progress.position ?? 0;

      console.log(
        '[PodcastPlayerService] Duration:',
        duration,
        'Position:',
        position
      );

      if (duration > 0 && position >= duration - 1) {
        console.log(
          '[PodcastPlayerService] ⏪ At end of track, seeking to start'
        );
        await TrackPlayer.seekTo(0);
      }

      console.log('[PodcastPlayerService] ▶️ Calling TrackPlayer.play()...');
      await TrackPlayer.play();
      console.log('[PodcastPlayerService] ✅ TrackPlayer.play() completed');

      usePodcastStore.getState().updatePlaybackState({
        isPlaying: true,
        isLoading: false,
      });
      console.log('[PodcastPlayerService] ✅ Play state updated');
    } catch (error) {
      console.error('[PodcastPlayerService] ❌ Play failed:', error);
      console.error(
        '[PodcastPlayerService] Error details:',
        JSON.stringify(error, null, 2)
      );
      usePodcastStore.getState().updatePlaybackState({
        isPlaying: false,
        isLoading: false,
      });
    }
  }

  async pause(): Promise<void> {
    console.log('[PodcastPlayerService] ⏸️ pause() called');
    await this.initialize();
    console.log('[PodcastPlayerService] ⏸️ Calling TrackPlayer.pause()...');
    await TrackPlayer.pause();
    console.log('[PodcastPlayerService] ✅ TrackPlayer.pause() completed');
    usePodcastStore.getState().updatePlaybackState({
      isPlaying: false,
    });
    console.log('[PodcastPlayerService] ✅ Pause state updated');
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
    await TrackPlayer.seekTo(clamped);
    store.updatePlaybackState({ position: clamped });
    const currentTrack = store.currentTrack;
    if (currentTrack) {
      await this.savePosition(this.getTrackKey(currentTrack), clamped);
    }
  }

  async setSpeed(speed: PlaybackSpeed): Promise<void> {
    await this.initialize();
    usePodcastStore.getState().setGlobalSpeed(speed);
    await TrackPlayer.setRate(speed);
    await this.repo.saveGlobalSpeed(speed);
  }

  getSpeed(): PlaybackSpeed {
    return usePodcastStore.getState().globalSpeed;
  }

  async getPosition(trackKey: string): Promise<number> {
    const persisted = await this.getPersistedTrackState(trackKey);
    return persisted?.position ?? 0;
  }

  async savePosition(trackKey: string, position: number): Promise<void> {
    if (!Number.isFinite(position)) {
      return;
    }
    await this.repo.saveUnitPosition(trackKey, position);
    const store = getPodcastStoreState();
    const currentTrack = store.currentTrack;
    if (currentTrack && this.getTrackKey(currentTrack) === trackKey) {
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
      await TrackPlayer.setRate(speed);
    }
  }

  private handlePlaybackProgress = (event: {
    position?: number;
    duration?: number;
    buffered?: number;
  }): void => {
    const store = usePodcastStore.getState();
    const { currentTrack, playbackState } = store;

    const position = event.position ?? playbackState.position;
    const buffered = event.buffered ?? playbackState.buffered;
    const eventDuration = event.duration ?? playbackState.duration;
    const fallbackDuration = currentTrack?.durationSeconds ?? 0;
    const duration = eventDuration > 0 ? eventDuration : fallbackDuration;

    // Log every 10 seconds to avoid spam
    if (Math.floor(position) % 10 === 0) {
      console.log('[PodcastPlayerService] 📊 Progress update:', {
        position: position.toFixed(1),
        duration,
        buffered,
      });
    }

    store.updatePlaybackState({
      position,
      buffered,
      duration,
    });

    if (this.currentTrackId && position > 0 && Math.floor(position) % 5 === 0) {
      void this.savePosition(this.currentTrackId, position);
    }
  };

  private handlePlaybackState = (event: { state?: TrackPlayerState }): void => {
    console.log('[PodcastPlayerService] 🎵 State change event:', event);
    const state = event.state;
    if (!state) {
      console.log('[PodcastPlayerService] ⚠️ State event with no state');
      return;
    }

    const isPlaying = state === TrackPlayerState.Playing;
    const isLoading =
      state === TrackPlayerState.Buffering ||
      state === TrackPlayerState.Connecting;

    console.log('[PodcastPlayerService] State interpreted as:', {
      rawState: state,
      isPlaying,
      isLoading,
    });

    usePodcastStore.getState().updatePlaybackState({
      isPlaying,
      isLoading,
    });

    if (state === TrackPlayerState.Stopped || state === TrackPlayerState.None) {
      console.log('[PodcastPlayerService] ⏹️ Playback stopped or none');
      usePodcastStore.getState().updatePlaybackState({ isPlaying: false });
    }
  };

  private async getPersistedTrackState(
    trackKey: string
  ): Promise<PersistedUnitState | null> {
    return this.repo.getUnitState(trackKey);
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
