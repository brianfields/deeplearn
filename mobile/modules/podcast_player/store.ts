/**
 * Podcast Player Store
 *
 * Zustand store for managing podcast playback state and UI flags.
 */

import { create } from 'zustand';
import type { PlaybackSpeed, PlaybackState, PodcastTrack } from './models';

const DEFAULT_SPEED: PlaybackSpeed = 1;

const DEFAULT_PLAYBACK_STATE: PlaybackState = {
  position: 0,
  duration: 0,
  buffered: 0,
  isPlaying: false,
  isLoading: false,
};

interface PodcastPlayerState {
  readonly currentTrack: PodcastTrack | null;
  readonly playbackState: PlaybackState;
  readonly globalSpeed: PlaybackSpeed;
  readonly isMinimized: boolean;
  setCurrentTrack: (track: PodcastTrack | null) => void;
  updatePlaybackState: (state: Partial<PlaybackState>) => void;
  setGlobalSpeed: (speed: PlaybackSpeed) => void;
  setMinimized: (minimized: boolean) => void;
  reset: () => void;
}

export const usePodcastStore = create<PodcastPlayerState>((set, get) => ({
  currentTrack: null,
  playbackState: DEFAULT_PLAYBACK_STATE,
  globalSpeed: DEFAULT_SPEED,
  isMinimized: false,
  setCurrentTrack: (track: PodcastTrack | null) => {
    set({ currentTrack: track });
  },
  updatePlaybackState: (state: Partial<PlaybackState>) => {
    const nextState: PlaybackState = {
      ...get().playbackState,
      ...state,
    };
    set({ playbackState: nextState });
  },
  setGlobalSpeed: (speed: PlaybackSpeed) => {
    set({ globalSpeed: speed });
  },
  setMinimized: (minimized: boolean) => {
    set({ isMinimized: minimized });
  },
  reset: () => {
    set({
      currentTrack: null,
      playbackState: DEFAULT_PLAYBACK_STATE,
      globalSpeed: DEFAULT_SPEED,
      isMinimized: false,
    });
  },
}));

export function getPodcastStoreState(): PodcastPlayerState {
  return usePodcastStore.getState();
}

export const PLAYBACK_SPEEDS: readonly PlaybackSpeed[] = [
  0.75, 1, 1.17, 1.33, 1.5, 1.67, 1.83, 2, 2.5, 3,
] as const;
