const mockPlayer = {
  playing: false,
  currentTime: 0,
  duration: 0,
  isBuffering: false,
  isLoaded: true,
  play: jest.fn(),
  pause: jest.fn(),
  seekTo: jest.fn().mockResolvedValue(undefined),
  setPlaybackRate: jest.fn(),
  remove: jest.fn(),
  addListener: jest.fn(),
  removeListener: jest.fn(),
};

export const createAudioPlayer = jest.fn(() => mockPlayer);

export const setAudioModeAsync = jest.fn().mockResolvedValue(undefined);

export const setIsAudioActiveAsync = jest.fn().mockResolvedValue(undefined);

export default {
  createAudioPlayer,
  setAudioModeAsync,
  setIsAudioActiveAsync,
};
