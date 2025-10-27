import { useCallback, useMemo } from 'react';
import type { PlaybackSpeed, PlaybackState, PodcastTrack } from '../models';
import { getPodcastPlayerService } from '../service';
import { usePodcastStore } from '../store';

interface PodcastPlayerHook {
  readonly loadPlaylist: (
    unitId: string,
    tracks: PodcastTrack[]
  ) => Promise<void>;
  readonly loadTrack: (track: PodcastTrack) => Promise<void>;
  readonly play: () => Promise<void>;
  readonly pause: () => Promise<void>;
  readonly skipForward: (seconds?: number) => Promise<void>;
  readonly skipBackward: (seconds?: number) => Promise<void>;
  readonly skipToNext: () => Promise<void>;
  readonly skipToPrevious: () => Promise<void>;
  readonly seekTo: (position: number) => Promise<void>;
  readonly setSpeed: (speed: PlaybackSpeed) => Promise<void>;
  readonly getSpeed: () => PlaybackSpeed;
  readonly currentTrack: PodcastTrack | null;
  readonly playbackState: PlaybackState;
  readonly globalSpeed: PlaybackSpeed;
  readonly autoplayEnabled: boolean;
  readonly toggleAutoplay: () => void;
}

const DEFAULT_SKIP_SECONDS = 15;

export function usePodcastPlayer(): PodcastPlayerHook {
  const service = useMemo(() => getPodcastPlayerService(), []);
  const currentTrack = usePodcastStore(state => state.currentTrack);
  const playbackState = usePodcastStore(state => state.playbackState);
  const globalSpeed = usePodcastStore(state => state.globalSpeed);
  const autoplayEnabled = usePodcastStore(state => state.autoplayEnabled);
  const storeToggleAutoplay = usePodcastStore(state => state.toggleAutoplay);

  const loadPlaylist = useCallback(
    async (unitId: string, tracks: PodcastTrack[]): Promise<void> => {
      await service.loadPlaylist(unitId, tracks);
    },
    [service]
  );

  const loadTrack = useCallback(
    async (track: PodcastTrack): Promise<void> => {
      await service.loadTrack(track);
    },
    [service]
  );

  const play = useCallback(async (): Promise<void> => {
    await service.play();
  }, [service]);

  const pause = useCallback(async (): Promise<void> => {
    await service.pause();
  }, [service]);

  const skipForward = useCallback(
    async (seconds: number = DEFAULT_SKIP_SECONDS): Promise<void> => {
      await service.skipForward(seconds);
    },
    [service]
  );

  const skipBackward = useCallback(
    async (seconds: number = DEFAULT_SKIP_SECONDS): Promise<void> => {
      await service.skipBackward(seconds);
    },
    [service]
  );

  const skipToNext = useCallback(async (): Promise<void> => {
    await service.skipToNext();
  }, [service]);

  const skipToPrevious = useCallback(async (): Promise<void> => {
    await service.skipToPrevious();
  }, [service]);

  const seekTo = useCallback(
    async (position: number): Promise<void> => {
      await service.seekTo(position);
    },
    [service]
  );

  const setSpeed = useCallback(
    async (speed: PlaybackSpeed): Promise<void> => {
      await service.setSpeed(speed);
    },
    [service]
  );

  const getSpeed = useCallback((): PlaybackSpeed => {
    return service.getSpeed();
  }, [service]);

  const toggleAutoplay = useCallback((): void => {
    storeToggleAutoplay();
  }, [storeToggleAutoplay]);

  return {
    loadPlaylist,
    loadTrack,
    play,
    pause,
    skipForward,
    skipBackward,
    skipToNext,
    skipToPrevious,
    seekTo,
    setSpeed,
    getSpeed,
    currentTrack,
    playbackState,
    globalSpeed,
    autoplayEnabled,
    toggleAutoplay,
  };
}
