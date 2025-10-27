import { useMemo } from 'react';
import type {
  PlaybackState,
  PlaybackSpeed,
  PodcastTrack,
  UnitPodcastPlaylist,
} from '../models';
import { usePodcastStore } from '../store';

export interface PodcastStateSnapshot {
  readonly currentTrack: PodcastTrack | null;
  readonly playbackState: PlaybackState;
  readonly globalSpeed: PlaybackSpeed;
  readonly isMinimized: boolean;
  readonly setMinimized: (minimized: boolean) => void;
  readonly playlist: UnitPodcastPlaylist | null;
  readonly autoplayEnabled: boolean;
}

export function usePodcastState(): PodcastStateSnapshot {
  const currentTrack = usePodcastStore(state => state.currentTrack);
  const playbackState = usePodcastStore(state => state.playbackState);
  const globalSpeed = usePodcastStore(state => state.globalSpeed);
  const isMinimized = usePodcastStore(state => state.isMinimized);
  const setMinimized = usePodcastStore(state => state.setMinimized);
  const playlist = usePodcastStore(state => state.playlist);
  const autoplayEnabled = usePodcastStore(state => state.autoplayEnabled);

  return useMemo(
    () => ({
      currentTrack,
      playbackState,
      globalSpeed,
      isMinimized,
      setMinimized,
      playlist,
      autoplayEnabled,
    }),
    [
      currentTrack,
      playbackState,
      globalSpeed,
      isMinimized,
      setMinimized,
      playlist,
      autoplayEnabled,
    ]
  );
}

export function useIsTrackActive(unitId?: string | null): boolean {
  return usePodcastStore(state => state.currentTrack?.unitId === unitId);
}
