const mockStatus = { isLoaded: true, isPlaying: false };

const createAsync = jest.fn(async () => ({
  sound: {
    playAsync: jest.fn().mockResolvedValue(undefined),
    pauseAsync: jest.fn().mockResolvedValue(undefined),
    unloadAsync: jest.fn().mockResolvedValue(undefined),
    getStatusAsync: jest.fn().mockResolvedValue(mockStatus),
    setOnPlaybackStatusUpdate: jest.fn(),
    setPositionAsync: jest.fn().mockResolvedValue(undefined),
  },
  status: mockStatus,
}));

export const Audio = {
  Sound: {
    createAsync,
  },
};

export default {
  Audio,
};
