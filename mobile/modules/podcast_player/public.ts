import { PodcastPlayer } from './components/PodcastPlayer';
import { MiniPlayer } from './components/MiniPlayer';
import { usePodcastPlayer } from './hooks/usePodcastPlayer';
import { usePodcastState, useIsTrackActive } from './hooks/usePodcastState';
import { useTrackPlayer } from './hooks/useTrackPlayer';
import { PLAYBACK_SPEEDS } from './store';

export {
  PodcastPlayer,
  MiniPlayer,
  usePodcastPlayer,
  usePodcastState,
  useIsTrackActive,
  useTrackPlayer,
  PLAYBACK_SPEEDS,
};

export type {
  PodcastTrack,
  PlaybackSpeed,
  UnitPodcastPlaylist,
} from './models';
