/**
 * Podcast Player Models
 *
 * Type definitions for podcast playback state and persistence.
 */

export type PlaybackSpeed =
  | 0.75
  | 1
  | 1.17
  | 1.33
  | 1.5
  | 1.67
  | 1.83
  | 2
  | 2.5
  | 3;

export interface PodcastTrack {
  readonly unitId: string;
  readonly title: string;
  readonly audioUrl: string;
  readonly durationSeconds: number;
  readonly transcript?: string | null;
  readonly artworkUrl?: string | null;
}

export interface PlaybackState {
  readonly position: number;
  readonly duration: number;
  readonly buffered: number;
  readonly isPlaying: boolean;
  readonly isLoading: boolean;
}

export interface PersistedUnitState {
  readonly position: number;
  readonly updatedAt: number;
}

export interface GlobalPlayerState {
  readonly speed: PlaybackSpeed;
}
