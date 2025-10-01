/**
 * Podcast Player Service
 *
 * Handles Track Player orchestration, persistence, and playback controls.
 */

import TrackPlayer, {
  AppKilledPlaybackBehavior,
  Capability,
} from 'react-native-track-player';
import type { InfrastructureProvider } from '../infrastructure/public';
import { infrastructureProvider } from '../infrastructure/public';
import type {
  GlobalPlayerState,
  PersistedUnitState,
  PlaybackSpeed,
  PodcastTrack,
} from './models';
import {
  PLAYBACK_SPEEDS,
  getPodcastStoreState,
  usePodcastStore,
} from './store';

const GLOBAL_STATE_KEY = 'podcast_player:global_speed';
const UNIT_STATE_PREFIX = 'podcast_player:unit:';

function isValidSpeed(speed: number): speed is PlaybackSpeed {
  return (PLAYBACK_SPEEDS as readonly number[]).includes(speed);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export class PodcastPlayerService {
  private infrastructure: InfrastructureProvider;
  private isInitialized = false;
  private initializationPromise: Promise<void> | null = null;
  private currentTrackId: string | null = null;

  constructor(infra: InfrastructureProvider = infrastructureProvider()) {
    this.infrastructure = infra;
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = (async () => {
      await TrackPlayer.setupPlayer();
      await TrackPlayer.updateOptions({
        capabilities: [
          Capability.Play,
          Capability.Pause,
          Capability.SeekTo,
          Capability.JumpForward,
          Capability.JumpBackward,
        ],
        compactCapabilities: [
          Capability.Play,
          Capability.Pause,
          Capability.JumpForward,
          Capability.JumpBackward,
        ],
        progressUpdateEventInterval: 1,
      });
      await TrackPlayer.setAppKilledPlaybackBehavior(
        AppKilledPlaybackBehavior.StopPlayback
      );
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
      await TrackPlayer.reset();
      this.currentTrackId = track.unitId;
      store.setCurrentTrack(track);
      store.updatePlaybackState({
        position: 0,
        duration: track.durationSeconds,
        isPlaying: false,
      });
    }

    const queue = await TrackPlayer.getQueue();
    const trackAlreadyQueued = queue.some(q => q.id === track.unitId);
    if (!trackAlreadyQueued) {
      if (isSameTrack) {
        await TrackPlayer.reset();
      }
      await TrackPlayer.add({
        id: track.unitId,
        url: track.audioUrl,
        title: track.title,
        artwork: track.artworkUrl ?? undefined,
        duration: track.durationSeconds,
      });
    }

    const persistedPosition = await this.getPersistedUnitState(track.unitId);
    const startPosition = clamp(
      persistedPosition?.position ?? 0,
      0,
      track.durationSeconds || Number.MAX_SAFE_INTEGER
    );

    if (startPosition > 0) {
      await TrackPlayer.seekTo(startPosition);
    }

    const speed = store.globalSpeed;
    await TrackPlayer.setRate(speed);

    store.setCurrentTrack(track);
    store.updatePlaybackState({
      position: startPosition,
      duration: track.durationSeconds,
      isPlaying: false,
      isLoading: false,
    });
  }

  async play(): Promise<void> {
    await this.initialize();
    await TrackPlayer.play();
    usePodcastStore.getState().updatePlaybackState({
      isPlaying: true,
      isLoading: false,
    });
  }

  async pause(): Promise<void> {
    await this.initialize();
    await TrackPlayer.pause();
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
    await TrackPlayer.seekTo(clamped);
    store.updatePlaybackState({ position: clamped });
    const trackId = store.currentTrack?.unitId;
    if (trackId) {
      await this.savePosition(trackId, clamped);
    }
  }

  async setSpeed(speed: PlaybackSpeed): Promise<void> {
    await this.initialize();
    usePodcastStore.getState().setGlobalSpeed(speed);
    await TrackPlayer.setRate(speed);
    const payload: GlobalPlayerState = { speed };
    await this.infrastructure.setStorageItem(
      GLOBAL_STATE_KEY,
      JSON.stringify(payload)
    );
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
    const payload: PersistedUnitState = {
      position,
      updatedAt: Date.now(),
    };
    await this.infrastructure.setStorageItem(
      this.getUnitKey(unitId),
      JSON.stringify(payload)
    );
    const store = getPodcastStoreState();
    if (store.currentTrack?.unitId === unitId) {
      store.updatePlaybackState({ position });
    }
  }

  getCurrentTrack(): PodcastTrack | null {
    return usePodcastStore.getState().currentTrack;
  }

  async hydrateGlobalSpeed(): Promise<void> {
    const raw = await this.infrastructure.getStorageItem(GLOBAL_STATE_KEY);
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as Partial<GlobalPlayerState>;
      if (
        parsed &&
        typeof parsed.speed === 'number' &&
        isValidSpeed(parsed.speed)
      ) {
        usePodcastStore.getState().setGlobalSpeed(parsed.speed);
        await TrackPlayer.setRate(parsed.speed);
      }
    } catch (error) {
      console.warn('[PodcastPlayer] Failed to parse global state', error);
    }
  }

  private async getPersistedUnitState(
    unitId: string
  ): Promise<PersistedUnitState | null> {
    const raw = await this.infrastructure.getStorageItem(
      this.getUnitKey(unitId)
    );
    if (!raw) {
      return null;
    }
    try {
      const parsed = JSON.parse(raw) as PersistedUnitState;
      if (
        typeof parsed === 'object' &&
        typeof parsed.position === 'number' &&
        typeof parsed.updatedAt === 'number'
      ) {
        return parsed;
      }
    } catch (error) {
      console.warn('[PodcastPlayer] Failed to parse unit state', error);
    }
    return null;
  }

  private getUnitKey(unitId: string): string {
    return `${UNIT_STATE_PREFIX}${unitId}:position`;
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
