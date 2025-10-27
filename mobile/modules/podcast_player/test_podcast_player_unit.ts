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

import TrackPlayer, {
  Event,
  State as TrackPlayerState,
} from 'react-native-track-player';
import {
  __resetPodcastPlayerServiceForTests,
  getPodcastPlayerService,
} from './service';
import { usePodcastStore } from './store';
import type { PodcastTrack } from './models';
import { infrastructureProvider } from '../infrastructure/public';

type TrackPlayerTestMock = typeof TrackPlayer & {
  __setProgress: (
    progress: Partial<{ position: number; duration: number }>
  ) => void;
  __setPlaybackState: (state: TrackPlayerState) => void;
  __resetMock: () => void;
  setupPlayer: jest.Mock;
  updateOptions: jest.Mock;
  setRepeatMode: jest.Mock;
  reset: jest.Mock;
  add: jest.Mock;
  setRate: jest.Mock;
  addEventListener: jest.Mock;
};

const trackPlayerMock = TrackPlayer as unknown as TrackPlayerTestMock;

describe('PodcastPlayerService', () => {
  const infraMock = infrastructureProvider as unknown as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    trackPlayerMock.__resetMock();
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
    lessonId: overrides.lessonId ?? null,
    lessonIndex: overrides.lessonIndex ?? null,
  });

  it('initializes audio and hydrates global speed', async () => {
    const storageState = (infraMock as any).__storageState as {
      map: Map<string, string>;
    };
    storageState.map.set(
      'podcast_player:global_speed',
      JSON.stringify({ speed: 1.5 })
    );

    const service = getPodcastPlayerService();
    await service.initialize();

    expect(trackPlayerMock.setupPlayer).toHaveBeenCalled();
    expect(trackPlayerMock.updateOptions).toHaveBeenCalledWith(
      expect.objectContaining({
        progressUpdateEventInterval: 1,
      })
    );
    expect(trackPlayerMock.setRepeatMode).toHaveBeenCalled();
    expect(trackPlayerMock.setRate).toHaveBeenCalledWith(1.5);
    expect(usePodcastStore.getState().globalSpeed).toBe(1.5);
  });

  it('loads tracks and enforces single-track playback', async () => {
    const service = getPodcastPlayerService();

    const firstTrack = createTrack({ unitId: 'unit-1', title: 'Unit 1' });
    await service.loadTrack(firstTrack);

    expect(trackPlayerMock.reset).toHaveBeenCalled();
    expect(trackPlayerMock.add).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'unit-1:intro',
        url: firstTrack.audioUrl,
        title: firstTrack.title,
      })
    );
    expect(usePodcastStore.getState().currentTrack?.unitId).toBe('unit-1');

    // Simulate progress update by updating both TrackPlayer mock and store
    trackPlayerMock.__setProgress({ position: 42, duration: 300 });
    usePodcastStore
      .getState()
      .updatePlaybackState({ position: 42, duration: 300 });

    const secondTrack = createTrack({ unitId: 'unit-2', title: 'Unit 2' });
    await service.loadTrack(secondTrack);

    const infraInstance = infraMock.mock.results[0].value;
    expect(infraInstance.setStorageItem).toHaveBeenCalledWith(
      'podcast_player:unit:unit-1:intro:position',
      expect.stringContaining('"position":42')
    );
    expect(usePodcastStore.getState().currentTrack?.unitId).toBe('unit-2');
  });

  it('loads playlists and keeps track indices in sync', async () => {
    const service = getPodcastPlayerService();

    const introTrack = createTrack({ unitId: 'unit-1', title: 'Intro' });
    const lessonTrack = createTrack({
      unitId: 'unit-1',
      title: 'Lesson 1',
      lessonId: 'lesson-1',
      lessonIndex: 0,
    });

    await service.loadPlaylist('unit-1', [introTrack, lessonTrack]);

    const store = usePodcastStore.getState();
    expect(store.playlist?.tracks).toHaveLength(2);
    expect(store.playlist?.unitId).toBe('unit-1');
    expect(store.playlist?.currentTrackIndex).toBe(0);

    await service.loadTrack(lessonTrack);
    expect(usePodcastStore.getState().playlist?.currentTrackIndex).toBe(1);
  });

  it('skips forward and backward within playlists', async () => {
    const service = getPodcastPlayerService();

    const intro = createTrack({ unitId: 'unit-1', title: 'Intro' });
    const lessonOne = createTrack({
      unitId: 'unit-1',
      title: 'Lesson 1',
      lessonId: 'lesson-1',
      lessonIndex: 0,
    });
    const lessonTwo = createTrack({
      unitId: 'unit-1',
      title: 'Lesson 2',
      lessonId: 'lesson-2',
      lessonIndex: 1,
    });

    await service.loadPlaylist('unit-1', [intro, lessonOne, lessonTwo]);
    await service.loadTrack(intro);

    await service.skipToNext();
    expect(usePodcastStore.getState().currentTrack?.lessonId).toBe('lesson-1');

    await service.skipToNext();
    expect(usePodcastStore.getState().currentTrack?.lessonId).toBe('lesson-2');

    await service.skipToPrevious();
    expect(usePodcastStore.getState().currentTrack?.lessonId).toBe('lesson-1');
  });

  it('autoplays next track when queue ends and autoplay is enabled', async () => {
    const service = getPodcastPlayerService();

    const intro = createTrack({ unitId: 'unit-1', title: 'Intro' });
    const lessonOne = createTrack({
      unitId: 'unit-1',
      title: 'Lesson 1',
      lessonId: 'lesson-1',
      lessonIndex: 0,
    });

    await service.loadPlaylist('unit-1', [intro, lessonOne]);
    await service.loadTrack(intro);
    await service.play();

    const addEventListenerMock = trackPlayerMock.addEventListener as jest.Mock;
    const queueEndedHandler = addEventListenerMock.mock.calls.find(
      call => call[0] === Event.PlaybackQueueEnded
    )?.[1] as (() => void) | undefined;
    expect(queueEndedHandler).toBeDefined();

    if (queueEndedHandler) {
      queueEndedHandler();
    }
    await new Promise(process.nextTick);

    expect(usePodcastStore.getState().currentTrack?.lessonId).toBe('lesson-1');
  });

  it('persists playback position and speed', async () => {
    const service = getPodcastPlayerService();

    await service.savePosition('unit-99:intro', 123.45);
    expect(
      (infraMock.mock.results[0].value as any).setStorageItem
    ).toHaveBeenCalledWith(
      'podcast_player:unit:unit-99:intro:position',
      expect.stringContaining('123.45')
    );
    await expect(service.getPosition('unit-99:intro')).resolves.toBeCloseTo(
      123.45
    );

    await service.setSpeed(1.33);
    expect(usePodcastStore.getState().globalSpeed).toBe(1.33);
    expect(
      (infraMock.mock.results[0].value as any).setStorageItem
    ).toHaveBeenCalledWith(
      'podcast_player:global_speed',
      expect.stringContaining('"speed":1.33')
    );
  });
});
