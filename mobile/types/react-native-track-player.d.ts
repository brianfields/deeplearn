declare module 'react-native-track-player' {
  export interface Track {
    id: string;
    url: string;
    title?: string;
    artwork?: string;
    duration?: number;
  }

  export type PlaybackStateValue = string;

  export interface Progress {
    position: number;
    duration: number;
    buffered: number;
  }

  export const State: Record<string, PlaybackStateValue>;
  export const Event: Record<string, string>;
  export const Capability: Record<string, string>;
  export const AppKilledPlaybackBehavior: Record<string, string>;

  export function addEventListener(
    event: string,
    listener: (...args: any[]) => void
  ): { remove: () => void };

  export function getState(): Promise<PlaybackStateValue>;
  export function getProgress(): Promise<Progress>;
  export function getQueue(): Promise<Track[]>;

  export function setupPlayer(): Promise<void>;
  export function updateOptions(
    options: Record<string, unknown>
  ): Promise<void>;
  export function setAppKilledPlaybackBehavior(behavior: string): Promise<void>;
  export function add(tracks: Track | Track[]): Promise<void>;
  export function reset(): Promise<void>;
  export function play(): Promise<void>;
  export function pause(): Promise<void>;
  export function seekTo(position: number): Promise<void>;
  export function setRate(rate: number): Promise<void>;
  export function registerPlaybackService(
    factory: () => () => Promise<void> | void
  ): void;

  const TrackPlayer: {
    setupPlayer: typeof setupPlayer;
    updateOptions: typeof updateOptions;
    setAppKilledPlaybackBehavior: typeof setAppKilledPlaybackBehavior;
    add: typeof add;
    reset: typeof reset;
    play: typeof play;
    pause: typeof pause;
    seekTo: typeof seekTo;
    setRate: typeof setRate;
    getState: typeof getState;
    getProgress: typeof getProgress;
    getQueue: typeof getQueue;
    addEventListener: typeof addEventListener;
    registerPlaybackService: typeof registerPlaybackService;
  };

  export default TrackPlayer;
}
