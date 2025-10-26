import { useEffect } from 'react';
import TrackPlayer, {
  Event,
  State,
  useTrackPlayerEvents,
} from 'react-native-track-player';
import { getPodcastPlayerService } from '../service';
import { usePodcastStore } from '../store';

export function useTrackPlayer(): void {
  const service = getPodcastPlayerService();

  useEffect(() => {
    console.log('[useTrackPlayer] 🔧 Initializing service...');
    service.initialize().catch(error => {
      console.warn('[PodcastPlayer] Failed to initialize', error);
    });
  }, [service]);

  // Listen to all playback events in a single hook call
  useTrackPlayerEvents(
    [Event.PlaybackProgressUpdated, Event.PlaybackState, Event.PlaybackError],
    async event => {
      console.log('[useTrackPlayer] 📡 Event received:', event.type);

      if (event.type === Event.PlaybackProgressUpdated) {
        console.log('[useTrackPlayer] 📊 Progress event:', event);
        const store = usePodcastStore.getState();
        const { currentTrack, playbackState } = store;

        const position = event.position ?? playbackState.position;
        const buffered = event.buffered ?? playbackState.buffered;
        const eventDuration = event.duration ?? playbackState.duration;
        const fallbackDuration = currentTrack?.durationSeconds ?? 0;
        const duration = eventDuration > 0 ? eventDuration : fallbackDuration;

        console.log('[useTrackPlayer] Updating position:', {
          position: position.toFixed(1),
          duration,
        });

        store.updatePlaybackState({
          position,
          buffered,
          duration,
        });

        // Save position every 5 seconds
        if (currentTrack && position > 0 && Math.floor(position) % 5 === 0) {
          void service.savePosition(currentTrack.unitId, position);
        }
      } else if (event.type === Event.PlaybackState) {
        console.log('[useTrackPlayer] 🎵 State event:', event);
        const playbackState = await TrackPlayer.getPlaybackState();
        console.log('[useTrackPlayer] Current state:', playbackState);

        const isPlaying = playbackState.state === State.Playing;
        const isLoading =
          playbackState.state === State.Buffering ||
          playbackState.state === State.Loading;

        console.log('[useTrackPlayer] Updating state:', {
          isPlaying,
          isLoading,
        });

        usePodcastStore.getState().updatePlaybackState({
          isPlaying,
          isLoading,
        });
      } else if (event.type === Event.PlaybackError) {
        console.error('[useTrackPlayer] 🚨 PLAYBACK ERROR:', event);
        console.error(
          '[useTrackPlayer] Error details:',
          JSON.stringify(event, null, 2)
        );
      }
    }
  );
}
