import { useEffect } from 'react';
import { getPodcastPlayerService } from '../service';

export function useTrackPlayer(): void {
  useEffect(() => {
    const service = getPodcastPlayerService();

    service.initialize().catch(error => {
      console.warn('[PodcastPlayer] Failed to initialize', error);
    });

    // expo-av handles status updates via the callback in service
    // No need for additional event listeners
  }, []);
}
