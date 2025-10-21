import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  jest,
} from '@jest/globals';
import renderer, { act } from 'react-test-renderer';

import { CacheManagementScreen } from './screens/CacheManagementScreen';
import type { CacheOverview } from './public';

const mockGoBack = jest.fn();
const mockNavigate = jest.fn();

jest.mock('@react-navigation/native', () => {
  const actual = jest.requireActual('@react-navigation/native');
  return {
    ...actual,
    useNavigation: () => ({
      goBack: mockGoBack,
      navigate: mockNavigate,
    }),
    useFocusEffect: (callback: () => void) => {
      callback();
    },
  };
});

const mockOfflineCacheProvider = jest.fn();
const mockContentProvider = jest.fn();
const mockInfrastructureProvider = jest.fn();

jest.mock('./public', () => ({
  offlineCacheProvider: () => mockOfflineCacheProvider(),
}));

jest.mock('../content/public', () => ({
  contentProvider: () => mockContentProvider(),
}));

jest.mock('../infrastructure/public', () => ({
  infrastructureProvider: () => mockInfrastructureProvider(),
}));

describe('CacheManagementScreen', () => {
  const mockGetCacheOverview = jest.fn<Promise<CacheOverview>, []>();
  const mockClearAll = jest.fn();
  const mockDeleteUnit = jest.fn();
  const mockMarkUnit = jest.fn();
  const mockSyncNow = jest.fn();
  const mockRequestUnitDownload = jest.fn();
  const mockGetNetworkStatus = jest.fn(() => ({ isConnected: true }));

  beforeEach(() => {
    mockGoBack.mockReset();
    mockNavigate.mockReset();
    mockGetCacheOverview.mockReset();
    mockClearAll.mockReset();
    mockDeleteUnit.mockReset();
    mockMarkUnit.mockReset();
    mockSyncNow.mockReset();
    mockRequestUnitDownload.mockReset();
    mockGetNetworkStatus.mockReset();

    mockOfflineCacheProvider.mockReturnValue({
      getCacheOverview: mockGetCacheOverview,
      clearAll: mockClearAll,
      deleteUnit: mockDeleteUnit,
      markUnitCacheMode: mockMarkUnit,
    });
    mockContentProvider.mockReturnValue({
      syncNow: mockSyncNow,
      requestUnitDownload: mockRequestUnitDownload,
    });
    mockInfrastructureProvider.mockReturnValue({
      getNetworkStatus: mockGetNetworkStatus,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders cache overview with network status and unit metrics', async () => {
    const overview: CacheOverview = {
      totalStorageBytes: 1048576,
      syncStatus: {
        pendingWrites: 2,
        cacheModeCounts: { minimal: 1, full: 0 },
        lastCursor: null,
        lastPulledAt: Date.now(),
        lastSyncAttempt: Date.now(),
        lastSyncResult: 'success',
        lastSyncError: null,
      },
      units: [
        {
          id: 'unit-1',
          title: 'Unit One',
          description: 'desc',
          learnerLevel: 'A1',
          isGlobal: true,
          updatedAt: Date.now(),
          schemaVersion: 1,
          downloadStatus: 'completed',
          cacheMode: 'minimal',
          downloadedAt: null,
          syncedAt: null,
          unitPayload: null,
          lessonCount: 0,
          assetCount: 0,
          downloadedAssets: 0,
          storageBytes: 0,
        },
      ],
    };
    mockGetCacheOverview.mockResolvedValue(overview);

    let component: renderer.ReactTestRenderer;
    await act(async () => {
      component = renderer.create(<CacheManagementScreen />);
    });

    const root = (component as renderer.ReactTestRenderer).root;
    expect(mockGetCacheOverview).toHaveBeenCalled();

    const storageText = root.findByProps({
      testID: 'cache-summary-total-storage',
    });
    expect(asString(storageText.props.children)).toContain('Storage used: 1 MB');

    const pendingWrites = root.findByProps({ testID: 'cache-pending-writes' });
    expect(asString(pendingWrites.props.children)).toContain('Pending writes: 2');

    const unitTitle = root.findByProps({ testID: 'cache-unit-unit-1-title' });
    expect(asString(unitTitle.props.children)).toBe('Unit One');
  });

  it('invokes cache actions from buttons', async () => {
    const overview: CacheOverview = {
      totalStorageBytes: 2048,
      syncStatus: {
        pendingWrites: 0,
        cacheModeCounts: { minimal: 1, full: 1 },
        lastCursor: null,
        lastPulledAt: null,
        lastSyncAttempt: 0,
        lastSyncResult: 'idle',
        lastSyncError: null,
      },
      units: [
        {
          id: 'unit-minimal',
          title: 'Minimal Unit',
          description: '',
          learnerLevel: 'A1',
          isGlobal: false,
          updatedAt: Date.now(),
          schemaVersion: 1,
          downloadStatus: 'completed',
          cacheMode: 'minimal',
          downloadedAt: null,
          syncedAt: null,
          unitPayload: null,
          lessonCount: 0,
          assetCount: 0,
          downloadedAssets: 0,
          storageBytes: 0,
        },
        {
          id: 'unit-full',
          title: 'Full Unit',
          description: '',
          learnerLevel: 'B2',
          isGlobal: true,
          updatedAt: Date.now(),
          schemaVersion: 1,
          downloadStatus: 'completed',
          cacheMode: 'full',
          downloadedAt: Date.now(),
          syncedAt: Date.now(),
          unitPayload: null,
          lessonCount: 3,
          assetCount: 2,
          downloadedAssets: 2,
          storageBytes: 1024,
        },
      ],
    };
    mockGetCacheOverview.mockResolvedValue(overview);

    let component: renderer.ReactTestRenderer;
    await act(async () => {
      component = renderer.create(<CacheManagementScreen />);
    });
    const root = (component as renderer.ReactTestRenderer).root;

    const syncButton = root.findByProps({ testID: 'cache-sync-button' });
    await act(async () => {
      await syncButton.props.onPress();
    });
    expect(mockSyncNow).toHaveBeenCalledTimes(1);

    const clearButton = root.findByProps({ testID: 'cache-clear-all-button' });
    await act(async () => {
      await clearButton.props.onPress();
    });
    expect(mockClearAll).toHaveBeenCalledTimes(1);

    const downloadButton = root.findByProps({
      testID: 'cache-unit-download-unit-minimal',
    });
    await act(async () => {
      await downloadButton.props.onPress();
    });
    expect(mockRequestUnitDownload).toHaveBeenCalledWith('unit-minimal');

    const downgradeButton = root.findByProps({
      testID: 'cache-unit-downgrade-unit-full',
    });
    await act(async () => {
      await downgradeButton.props.onPress();
    });
    expect(mockMarkUnit).toHaveBeenCalledWith('unit-full', 'minimal');

    const deleteButton = root.findByProps({
      testID: 'cache-unit-delete-unit-full',
    });
    await act(async () => {
      await deleteButton.props.onPress();
    });
    expect(mockDeleteUnit).toHaveBeenCalledWith('unit-full');
  });
});

function asString(children: unknown): string {
  if (children === undefined || children === null) {
    return '';
  }
  if (Array.isArray(children)) {
    return children.map(asString).join('');
  }
  return String(children);
}
