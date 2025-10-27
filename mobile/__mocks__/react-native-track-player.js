const listeners = new Map();

const Event = {
  PlaybackProgressUpdated: 'playback-progress',
  PlaybackState: 'playback-state',
  PlaybackQueueEnded: 'playback-queue-ended',
  RemotePlay: 'remote-play',
  RemotePause: 'remote-pause',
  RemoteStop: 'remote-stop',
  RemoteSeek: 'remote-seek',
  RemoteNext: 'remote-next',
  RemotePrevious: 'remote-previous',
};

const State = {
  None: 'none',
  Ready: 'ready',
  Playing: 'playing',
  Paused: 'paused',
  Stopped: 'stopped',
  Buffering: 'buffering',
  Connecting: 'connecting',
};

const Capability = {
  Play: 'play',
  Pause: 'pause',
  Stop: 'stop',
  SeekTo: 'seekTo',
  SkipToNext: 'skipToNext',
  SkipToPrevious: 'skipToPrevious',
};

const RepeatMode = {
  Off: 'off',
};

const AppKilledPlaybackBehavior = {
  StopPlaybackAndRemoveNotification: 'stop',
};

const defaultProgress = { position: 0, duration: 0, buffered: 0 };
let progress = { ...defaultProgress };
let playbackState = State.Ready;

const addEventListener = jest.fn((event, handler) => {
  listeners.set(event, handler);
  return {
    remove: jest.fn(() => {
      listeners.delete(event);
    }),
  };
});

const setupPlayer = jest.fn(async () => {});
const updateOptions = jest.fn(async () => {});
const setRepeatMode = jest.fn(async () => {});
const reset = jest.fn(async () => {});
const add = jest.fn(async () => {});
const seekTo = jest.fn(async position => {
  progress = { ...progress, position };
});
const setRate = jest.fn(async () => {});
const play = jest.fn(async () => {
  playbackState = State.Playing;
});
const pause = jest.fn(async () => {
  playbackState = State.Paused;
});
const getProgress = jest.fn(async () => progress);
const getActiveTrack = jest.fn(async () => null);
const getPlaybackState = jest.fn(async () => playbackState);
const getState = jest.fn(async () => playbackState);
const destroy = jest.fn(async () => {});
const registerPlaybackService = jest.fn();

function emit(event, payload) {
  const handler = listeners.get(event);
  if (handler) {
    handler(payload);
  }
}

function __setProgress(nextProgress) {
  progress = { ...progress, ...nextProgress };
  emit(Event.PlaybackProgressUpdated, progress);
}

function __setPlaybackState(nextState) {
  playbackState = nextState;
  emit(Event.PlaybackState, { state: nextState });
}

function __resetMock() {
  listeners.clear();
  progress = { ...defaultProgress };
  playbackState = State.Ready;
  setupPlayer.mockClear();
  updateOptions.mockClear();
  setRepeatMode.mockClear();
  addEventListener.mockClear();
  reset.mockClear();
  add.mockClear();
  seekTo.mockClear();
  setRate.mockClear();
  play.mockClear();
  pause.mockClear();
  getProgress.mockClear();
  getActiveTrack.mockClear();
  getPlaybackState.mockClear();
  getState.mockClear();
  destroy.mockClear();
  registerPlaybackService.mockClear();
}

const TrackPlayer = {
  setupPlayer,
  updateOptions,
  setRepeatMode,
  addEventListener,
  reset,
  add,
  seekTo,
  setRate,
  play,
  pause,
  getProgress,
  getActiveTrack,
  getPlaybackState,
  getState,
  destroy,
  registerPlaybackService,
  __setProgress,
  __setPlaybackState,
  __resetMock,
  Event,
  State,
  Capability,
  RepeatMode,
  AppKilledPlaybackBehavior,
};

module.exports = {
  ...TrackPlayer,
  Event,
  State,
  Capability,
  RepeatMode,
  AppKilledPlaybackBehavior,
  default: TrackPlayer,
};
