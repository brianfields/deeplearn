import TrackPlayer, { Event } from 'react-native-track-player';
import { getPodcastPlayerService } from './service';

export default async function trackPlayerBackgroundService(): Promise<void> {
  TrackPlayer.addEventListener(Event.RemotePlay, () => {
    void getPodcastPlayerService().play();
  });

  TrackPlayer.addEventListener(Event.RemotePause, () => {
    void getPodcastPlayerService().pause();
  });

  TrackPlayer.addEventListener(Event.RemoteStop, () => {
    void getPodcastPlayerService().pause();
  });

  TrackPlayer.addEventListener(
    Event.RemoteSeek,
    (event: { position?: number }) => {
      void getPodcastPlayerService().seekTo(event.position ?? 0);
    }
  );

  TrackPlayer.addEventListener(Event.RemotePrevious, () => {
    void getPodcastPlayerService().seekTo(0);
  });

  TrackPlayer.addEventListener(Event.RemoteNext, () => {
    const service = getPodcastPlayerService();
    const currentTrack = service.getCurrentTrack();
    if (currentTrack) {
      void service.seekTo(currentTrack.durationSeconds);
    }
  });
}
