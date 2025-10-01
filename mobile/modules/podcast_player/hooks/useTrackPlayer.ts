import { useEffect } from 'react';
import TrackPlayer, { Event, State } from 'react-native-track-player';
import { getPodcastPlayerService } from '../service';
import { usePodcastStore } from '../store';

export function useTrackPlayer(): void {
  useEffect(() => {
    let isMounted = true;
    const service = getPodcastPlayerService();

    service.initialize().catch(error => {
      console.warn('[PodcastPlayer] Failed to initialize', error);
    });

    const syncPlaybackState = async () => {
      try {
        const state = await TrackPlayer.getState();
        if (!isMounted) {
          return;
        }
        usePodcastStore.getState().updatePlaybackState({
          isPlaying: state === State.Playing,
          isLoading: state === State.Loading || state === State.Buffering,
        });
      } catch (error) {
        console.warn('[PodcastPlayer] Failed to sync playback state', error);
      }
    };

    const syncProgress = async () => {
      try {
        const progress = await TrackPlayer.getProgress();
        if (!isMounted) {
          return;
        }
        usePodcastStore.getState().updatePlaybackState({
          position: progress.position,
          duration: progress.duration,
          buffered: progress.buffered,
        });
        const currentTrack = usePodcastStore.getState().currentTrack;
        if (currentTrack) {
          await service.savePosition(currentTrack.unitId, progress.position);
        }
      } catch (error) {
        console.warn('[PodcastPlayer] Failed to sync progress', error);
      }
    };

    syncPlaybackState().catch(() => {});
    syncProgress().catch(() => {});

    const playbackSub = TrackPlayer.addEventListener(
      Event.PlaybackState,
      payload => {
        usePodcastStore.getState().updatePlaybackState({
          isPlaying: payload.state === State.Playing,
          isLoading:
            payload.state === State.Loading ||
            payload.state === State.Buffering,
        });
      }
    );

    const trackChangeSub = TrackPlayer.addEventListener(
      Event.PlaybackTrackChanged,
      () => {
        syncProgress().catch(() => {});
      }
    );

    const interval = setInterval(() => {
      syncProgress().catch(() => {});
    }, 1000);

    return () => {
      isMounted = false;
      playbackSub?.remove?.();
      trackChangeSub?.remove?.();
      clearInterval(interval);
    };
  }, []);
}
