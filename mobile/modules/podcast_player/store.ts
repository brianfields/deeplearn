/**
 * Podcast Player Store
 *
 * Zustand store for managing podcast playback state and UI flags.
 */

import { create } from 'zustand';
import type {
  PlaybackSpeed,
  PlaybackState,
  PodcastTrack,
  UnitPodcastPlaylist,
} from './models';

const DEFAULT_SPEED: PlaybackSpeed = 1;

const DEFAULT_PLAYBACK_STATE: PlaybackState = {
  position: 0,
  duration: 0,
  buffered: 0,
  isPlaying: false,
  isLoading: false,
};

export type PlaybackUIState = 'idle' | 'playing' | 'paused';

interface PodcastPlayerState {
  readonly currentTrack: PodcastTrack | null;
  readonly playlist: UnitPodcastPlaylist | null;
  readonly playbackState: PlaybackState;
  readonly globalSpeed: PlaybackSpeed;
  readonly isMinimized: boolean;
  readonly autoplayEnabled: boolean;
  readonly playbackUIState: PlaybackUIState;
  // The lessonId that the user manually skipped away from via audio controls
  // (prevents that specific lesson page from forcing the track back)
  readonly lessonIdSkippedFrom: string | null;
  setCurrentTrack: (track: PodcastTrack | null) => void;
  setPlaylist: (playlist: UnitPodcastPlaylist | null) => void;
  setCurrentTrackIndex: (index: number) => void;
  updatePlaybackState: (state: Partial<PlaybackState>) => void;
  setGlobalSpeed: (speed: PlaybackSpeed) => void;
  setMinimized: (minimized: boolean) => void;
  setPlaybackUIState: (state: PlaybackUIState) => void;
  setLessonIdSkippedFrom: (lessonId: string | null) => void;
  toggleAutoplay: () => void;
  reset: () => void;
}

export const usePodcastStore = create<PodcastPlayerState>((set, get) => ({
  currentTrack: null,
  playlist: null,
  playbackState: DEFAULT_PLAYBACK_STATE,
  globalSpeed: DEFAULT_SPEED,
  isMinimized: false,
  autoplayEnabled: true,
  playbackUIState: 'idle',
  lessonIdSkippedFrom: null,
  setCurrentTrack: (track: PodcastTrack | null) => {
    set({ currentTrack: track });
  },
  setPlaylist: (playlist: UnitPodcastPlaylist | null) => {
    set(state => {
      if (!playlist) {
        return {
          playlist: null,
          currentTrack: null,
          playbackState: DEFAULT_PLAYBACK_STATE,
        };
      }

      const { currentTrack: existing } = state;
      const nextTrack = playlist.tracks[playlist.currentTrackIndex] ?? null;
      const matchedTrack = existing
        ? (playlist.tracks.find(track =>
            track.lessonId
              ? track.lessonId === existing.lessonId
              : !track.lessonId &&
                !existing.lessonId &&
                track.unitId === existing.unitId
          ) ?? null)
        : null;

      return {
        playlist,
        currentTrack: matchedTrack ?? nextTrack,
      };
    });
  },
  setCurrentTrackIndex: (index: number) => {
    set(state => {
      const playlist = state.playlist;
      if (!playlist) {
        return {};
      }

      const clampedIndex = Math.max(
        0,
        Math.min(index, playlist.tracks.length - 1)
      );
      const nextTrack = playlist.tracks[clampedIndex] ?? null;

      return {
        playlist: {
          ...playlist,
          currentTrackIndex: clampedIndex,
        },
        currentTrack: nextTrack,
      };
    });
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
  setPlaybackUIState: (state: PlaybackUIState) => {
    set({ playbackUIState: state });
  },
  setLessonIdSkippedFrom: (lessonId: string | null) => {
    set({ lessonIdSkippedFrom: lessonId });
  },
  toggleAutoplay: () => {
    set(state => ({ autoplayEnabled: !state.autoplayEnabled }));
  },
  reset: () => {
    set({
      currentTrack: null,
      playlist: null,
      playbackState: DEFAULT_PLAYBACK_STATE,
      globalSpeed: DEFAULT_SPEED,
      isMinimized: false,
      autoplayEnabled: true,
      playbackUIState: 'idle',
      lessonIdSkippedFrom: null,
    });
  },
}));

export function getPodcastStoreState(): PodcastPlayerState {
  return usePodcastStore.getState();
}

export const PLAYBACK_SPEEDS: readonly PlaybackSpeed[] = [
  0.75, 1, 1.17, 1.33, 1.5, 1.67, 1.83, 2, 2.5, 3,
] as const;
