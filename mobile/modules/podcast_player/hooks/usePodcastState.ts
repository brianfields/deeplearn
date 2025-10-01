import { useMemo } from 'react';
import type { PlaybackState, PlaybackSpeed, PodcastTrack } from '../models';
import { usePodcastStore } from '../store';

export interface PodcastStateSnapshot {
  readonly currentTrack: PodcastTrack | null;
  readonly playbackState: PlaybackState;
  readonly globalSpeed: PlaybackSpeed;
  readonly isMinimized: boolean;
  readonly setMinimized: (minimized: boolean) => void;
}

export function usePodcastState(): PodcastStateSnapshot {
  const currentTrack = usePodcastStore(state => state.currentTrack);
  const playbackState = usePodcastStore(state => state.playbackState);
  const globalSpeed = usePodcastStore(state => state.globalSpeed);
  const isMinimized = usePodcastStore(state => state.isMinimized);
  const setMinimized = usePodcastStore(state => state.setMinimized);

  return useMemo(
    () => ({
      currentTrack,
      playbackState,
      globalSpeed,
      isMinimized,
      setMinimized,
    }),
    [currentTrack, playbackState, globalSpeed, isMinimized, setMinimized]
  );
}

export function useIsTrackActive(unitId?: string | null): boolean {
  return usePodcastStore(state => state.currentTrack?.unitId === unitId);
}
