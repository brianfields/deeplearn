import { useMemo } from 'react';
import type {
  PlaybackState,
  PlaybackSpeed,
  PodcastTrack,
  UnitPodcastPlaylist,
} from '../models';
import { usePodcastStore, type PlaybackUIState } from '../store';

export interface PodcastStateSnapshot {
  readonly currentTrack: PodcastTrack | null;
  readonly playbackState: PlaybackState;
  readonly globalSpeed: PlaybackSpeed;
  readonly isMinimized: boolean;
  readonly setMinimized: (minimized: boolean) => void;
  readonly playlist: UnitPodcastPlaylist | null;
  readonly autoplayEnabled: boolean;
  readonly playbackUIState: PlaybackUIState;
  readonly lessonIdSkippedFrom: string | null;
}

export function usePodcastState(): PodcastStateSnapshot {
  const currentTrack = usePodcastStore(state => state.currentTrack);
  const playbackState = usePodcastStore(state => state.playbackState);
  const globalSpeed = usePodcastStore(state => state.globalSpeed);
  const isMinimized = usePodcastStore(state => state.isMinimized);
  const setMinimized = usePodcastStore(state => state.setMinimized);
  const playlist = usePodcastStore(state => state.playlist);
  const autoplayEnabled = usePodcastStore(state => state.autoplayEnabled);
  const playbackUIState = usePodcastStore(state => state.playbackUIState);
  const lessonIdSkippedFrom = usePodcastStore(
    state => state.lessonIdSkippedFrom
  );

  return useMemo(
    () => ({
      currentTrack,
      playbackState,
      globalSpeed,
      isMinimized,
      setMinimized,
      playlist,
      autoplayEnabled,
      playbackUIState,
      lessonIdSkippedFrom,
    }),
    [
      currentTrack,
      playbackState,
      globalSpeed,
      isMinimized,
      setMinimized,
      playlist,
      autoplayEnabled,
      playbackUIState,
      lessonIdSkippedFrom,
    ]
  );
}

export function useIsTrackActive(unitId?: string | null): boolean {
  return usePodcastStore(state => state.currentTrack?.unitId === unitId);
}
