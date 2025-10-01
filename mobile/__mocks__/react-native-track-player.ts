const State = {
  None: 'none',
  Loading: 'loading',
  Ready: 'ready',
  Playing: 'playing',
  Paused: 'paused',
  Stopped: 'stopped',
  Buffering: 'buffering',
} as const;

type StateValue = (typeof State)[keyof typeof State];

type Progress = {
  position: number;
  duration: number;
  buffered: number;
};

const Capability = {
  Play: 'play',
  Pause: 'pause',
  Stop: 'stop',
  SeekTo: 'seekTo',
  SkipToNext: 'skipToNext',
  SkipToPrevious: 'skipToPrevious',
  JumpForward: 'jumpForward',
  JumpBackward: 'jumpBackward',
  TogglePlayPause: 'togglePlayPause',
  SetRating: 'setRating',
  PlayFromId: 'playFromId',
  PlayFromSearch: 'playFromSearch',
  SetSpeed: 'setSpeed',
} as const;

const RepeatMode = {
  Off: 'off',
  Track: 'track',
  Queue: 'queue',
} as const;

const Event = {
  RemotePlay: 'remote-play',
  RemotePause: 'remote-pause',
  RemoteStop: 'remote-stop',
  RemoteNext: 'remote-next',
  RemotePrevious: 'remote-previous',
  RemoteSeek: 'remote-seek',
  RemoteJumpForward: 'remote-jump-forward',
  RemoteJumpBackward: 'remote-jump-backward',
  PlaybackState: 'playback-state',
  PlaybackError: 'playback-error',
  PlaybackTrackChanged: 'playback-track-changed',
  PlaybackQueueEnded: 'playback-queue-ended',
} as const;

const AppKilledPlaybackBehavior = {
  ContinuePlayback: 'continue-playback',
  StopPlayback: 'stop-playback',
} as const;

type Track = {
  id: string;
  url: string;
  title?: string;
  artist?: string;
  artwork?: string;
};

type TrackLike = Track | Track[];

type MaybeTrackId = string | null;

type RemoveArg = string | string[] | undefined;

type SeekArg = number;

const TrackPlayer = {
  setupPlayer: jest.fn(async (): Promise<void> => {}),
  updateOptions: jest.fn(async (): Promise<void> => {}),
  addEventListener: jest.fn(
    (_event: string, _listener: (...args: any[]) => void) => ({
      remove: jest.fn(),
    })
  ),
  registerPlaybackService: jest.fn(() => {}),
  add: jest.fn(async (_tracks: TrackLike): Promise<void> => {}),
  load: jest.fn(async (_tracks: TrackLike): Promise<void> => {}),
  setQueue: jest.fn(async (_tracks: TrackLike): Promise<void> => {}),
  play: jest.fn(async (): Promise<void> => {}),
  pause: jest.fn(async (): Promise<void> => {}),
  stop: jest.fn(async (): Promise<void> => {}),
  reset: jest.fn(async (): Promise<void> => {}),
  destroy: jest.fn(async (): Promise<void> => {}),
  remove: jest.fn(async (_tracks: RemoveArg): Promise<void> => {}),
  skip: jest.fn(async (_trackId: string): Promise<void> => {}),
  skipToNext: jest.fn(async (): Promise<void> => {}),
  skipToPrevious: jest.fn(async (): Promise<void> => {}),
  seekTo: jest.fn(async (_position: SeekArg): Promise<void> => {}),
  getCurrentTrack: jest.fn(async (): Promise<MaybeTrackId> => null),
  getTrack: jest.fn(async (_trackId: string): Promise<Track | null> => null),
  getState: jest.fn(async (): Promise<StateValue> => State.None),
  getProgress: jest.fn(
    async (): Promise<Progress> => ({
      position: 0,
      duration: 0,
      buffered: 0,
    })
  ),
  setRate: jest.fn(async (_rate: number): Promise<void> => {}),
  setVolume: jest.fn(async (_volume: number): Promise<void> => {}),
  setRepeatMode: jest.fn(
    async (
      _mode: (typeof RepeatMode)[keyof typeof RepeatMode]
    ): Promise<void> => {}
  ),
  setAppKilledPlaybackBehavior: jest.fn(
    async (
      _behavior: (typeof AppKilledPlaybackBehavior)[keyof typeof AppKilledPlaybackBehavior]
    ): Promise<void> => {}
  ),
  getQueue: jest.fn(async (): Promise<Track[]> => []),
  setMetadata: jest.fn(
    async (_metadata: Record<string, unknown>): Promise<void> => {}
  ),
};

export const useTrackPlayerEvents = jest.fn();
export const useProgress = jest.fn(
  (): Progress => ({
    position: 0,
    duration: 0,
    buffered: 0,
  })
);

export { AppKilledPlaybackBehavior, Capability, Event, RepeatMode, State };

export default TrackPlayer;
