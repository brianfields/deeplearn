jest.mock('../infrastructure/public', () => {
  const storageState = { map: new Map<string, string>() };
  const createInfra = () => ({
    request: jest.fn(),
    getNetworkStatus: jest.fn(),
    checkHealth: jest.fn(),
    getStorageItem: jest.fn(async (key: string) => {
      return storageState.map.get(key) ?? null;
    }),
    setStorageItem: jest.fn(async (key: string, value: string) => {
      storageState.map.set(key, value);
    }),
    removeStorageItem: jest.fn(async (key: string) => {
      storageState.map.delete(key);
    }),
    getStorageStats: jest.fn(async () => ({
      entries: storageState.map.size,
      size: Array.from(storageState.map.values()).reduce(
        (total, value) => total + value.length,
        0
      ),
    })),
    clearStorage: jest.fn(async () => {
      storageState.map.clear();
    }),
  });
  const providerMock = jest.fn(() => createInfra());
  (providerMock as any).__storageState = storageState;
  (providerMock as any).__createInfra = createInfra;
  return {
    infrastructureProvider: providerMock,
  };
});

import TrackPlayer from 'react-native-track-player';
import {
  __resetPodcastPlayerServiceForTests,
  getPodcastPlayerService,
} from './service';
import { usePodcastStore } from './store';
import type { PodcastTrack } from './models';
import { infrastructureProvider } from '../infrastructure/public';

describe('PodcastPlayerService', () => {
  const infraMock = infrastructureProvider as unknown as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    const storageState = (infraMock as any).__storageState as {
      map: Map<string, string>;
    };
    storageState.map.clear();
    infraMock.mockImplementation(() => {
      const base = (infraMock as any).__createInfra();
      return base;
    });
    __resetPodcastPlayerServiceForTests();
  });

  const createTrack = (
    overrides: Partial<PodcastTrack> = {}
  ): PodcastTrack => ({
    unitId: overrides.unitId ?? 'unit-a',
    title: overrides.title ?? 'Unit Podcast',
    audioUrl: overrides.audioUrl ?? 'https://example.com/audio.mp3',
    durationSeconds: overrides.durationSeconds ?? 300,
    transcript: overrides.transcript ?? 'Transcript',
  });

  it('initializes Track Player and hydrates global speed', async () => {
    const storageState = (infraMock as any).__storageState as {
      map: Map<string, string>;
    };
    storageState.map.set(
      'podcast_player:global_speed',
      JSON.stringify({ speed: 1.5 })
    );

    const service = getPodcastPlayerService();
    await service.initialize();

    expect(TrackPlayer.setupPlayer).toHaveBeenCalledTimes(1);
    expect(TrackPlayer.updateOptions).toHaveBeenCalledTimes(1);
    expect(usePodcastStore.getState().globalSpeed).toBe(1.5);
    expect(TrackPlayer.setRate).toHaveBeenCalledWith(1.5);
  });

  it('loads tracks and enforces single-track playback', async () => {
    const service = getPodcastPlayerService();

    const firstTrack = createTrack({ unitId: 'unit-1', title: 'Unit 1' });
    await service.loadTrack(firstTrack);

    expect(TrackPlayer.add).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'unit-1', url: firstTrack.audioUrl })
    );
    expect(usePodcastStore.getState().currentTrack?.unitId).toBe('unit-1');

    usePodcastStore
      .getState()
      .updatePlaybackState({ position: 42, duration: 300 });

    const secondTrack = createTrack({ unitId: 'unit-2', title: 'Unit 2' });
    await service.loadTrack(secondTrack);

    const infraInstance = infraMock.mock.results[0].value;
    expect(infraInstance.setStorageItem).toHaveBeenCalledWith(
      'podcast_player:unit:unit-1:position',
      expect.stringContaining('"position":42')
    );
    expect(TrackPlayer.reset).toHaveBeenCalledTimes(2);
    expect(TrackPlayer.add).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'unit-2', url: secondTrack.audioUrl })
    );
    expect(usePodcastStore.getState().currentTrack?.unitId).toBe('unit-2');
  });

  it('persists playback position and speed', async () => {
    const service = getPodcastPlayerService();

    await service.savePosition('unit-99', 123.45);
    expect(
      (infraMock.mock.results[0].value as any).setStorageItem
    ).toHaveBeenCalledWith(
      'podcast_player:unit:unit-99:position',
      expect.stringContaining('123.45')
    );
    await expect(service.getPosition('unit-99')).resolves.toBeCloseTo(123.45);

    await service.setSpeed(1.25);
    expect(usePodcastStore.getState().globalSpeed).toBe(1.25);
    expect(TrackPlayer.setRate).toHaveBeenCalledWith(1.25);
    expect(
      (infraMock.mock.results[0].value as any).setStorageItem
    ).toHaveBeenCalledWith(
      'podcast_player:global_speed',
      expect.stringContaining('"speed":1.25')
    );
  });
});
