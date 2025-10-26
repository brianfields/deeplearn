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
import type { PersistedUnitState, PlaybackSpeed, PodcastTrack } from './models';
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
      await TrackPlayer.setupPlayer();
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
      await TrackPlayer.setRepeatMode(RepeatMode.Off);
      this.attachEventListeners();
      await this.hydrateGlobalSpeed();
      this.isInitialized = true;
    })();

    try {
      await this.initializationPromise;
    } finally {
      this.initializationPromise = null;
    }
  }

  private attachEventListeners(): void {
    if (!this.progressSubscription) {
      this.progressSubscription = TrackPlayer.addEventListener(
        Event.PlaybackProgressUpdated,
        this.handlePlaybackProgress
      );
    }

    if (!this.stateSubscription) {
      this.stateSubscription = TrackPlayer.addEventListener(
        Event.PlaybackState,
        this.handlePlaybackState
      );
    }
  }

  async loadTrack(track: PodcastTrack): Promise<void> {
    await this.initialize();
    const store = getPodcastStoreState();
    const { playbackState } = store;

    store.updatePlaybackState({ isLoading: true });

    if (this.currentTrackId && this.currentTrackId !== track.unitId) {
      await this.savePosition(this.currentTrackId, playbackState.position);
    }

    await TrackPlayer.reset();

    this.currentTrackId = track.unitId;
    store.setCurrentTrack(track);
    store.updatePlaybackState({
      position: 0,
      duration: track.durationSeconds,
      buffered: 0,
      isPlaying: false,
    });

    const persistedState = await this.getPersistedUnitState(track.unitId);
    const startPosition = clamp(
      persistedState?.position ?? 0,
      0,
      track.durationSeconds || Number.MAX_SAFE_INTEGER
    );

    await TrackPlayer.add({
      id: track.unitId,
      url: track.audioUrl,
      title: track.title,
      artist: DEFAULT_ARTIST,
      duration: track.durationSeconds,
    });

    const speed = store.globalSpeed;
    await TrackPlayer.setRate(speed);

    if (startPosition > 0) {
      await TrackPlayer.seekTo(startPosition);
    }

    store.updatePlaybackState({
      position: startPosition,
      duration: track.durationSeconds,
      buffered: 0,
      isPlaying: false,
      isLoading: false,
    });
  }

  async play(): Promise<void> {
    await this.initialize();
    if (!this.currentTrackId) {
      console.warn('[PodcastPlayer] Cannot play: no active track');
      return;
    }

    try {
      const progress = await TrackPlayer.getProgress();
      const duration = progress.duration ?? 0;
      const position = progress.position ?? 0;

      if (duration > 0 && position >= duration - 1) {
        await TrackPlayer.seekTo(0);
      }

      await TrackPlayer.play();

      usePodcastStore.getState().updatePlaybackState({
        isPlaying: true,
        isLoading: false,
      });
    } catch (error) {
      console.error('[PodcastPlayer] Play failed:', error);
      usePodcastStore.getState().updatePlaybackState({
        isPlaying: false,
        isLoading: false,
      });
    }
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
    const state = event.state;
    if (!state) {
      return;
    }

    const isPlaying = state === TrackPlayerState.Playing;
    const isLoading =
      state === TrackPlayerState.Buffering ||
      state === TrackPlayerState.Connecting;

    usePodcastStore.getState().updatePlaybackState({
      isPlaying,
      isLoading,
    });

    if (state === TrackPlayerState.Stopped || state === TrackPlayerState.None) {
      usePodcastStore.getState().updatePlaybackState({ isPlaying: false });
    }
  };

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
