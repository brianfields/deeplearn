import { useEffect } from 'react';
import { getPodcastPlayerService } from '../service';

export function useTrackPlayer(): void {
  useEffect(() => {
    const service = getPodcastPlayerService();

    service.initialize().catch(error => {
      console.warn('[PodcastPlayer] Failed to initialize', error);
    });

    // The service wires TrackPlayer events to the store, so no extra listeners here
  }, []);
}
