import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import {
  ArrowLeft,
  Cloud,
  CloudOff,
  Download,
  HardDrive,
  RotateCcw,
  Trash2,
} from 'lucide-react-native';

import {
  offlineCacheProvider,
  type CacheOverview,
} from '../public';
import { contentProvider } from '../../content/public';
import { infrastructureProvider } from '../../infrastructure/public';
import { Button } from '../../ui_system/components/Button';
import { Text, uiSystemProvider, useHaptics } from '../../ui_system/public';
import type { LearningStackParamList } from '../../../types';

interface UnitActionState {
  unitId: string;
  action: 'download' | 'downgrade' | 'delete';
}

type CacheManagementNavigation = NativeStackNavigationProp<
  LearningStackParamList,
  'CacheManagement'
>;

export function CacheManagementScreen(): React.ReactElement {
  const offlineCache = offlineCacheProvider();
  const content = contentProvider();
  const infrastructure = infrastructureProvider();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const navigation = useNavigation<CacheManagementNavigation>();
  const { trigger } = useHaptics();

  const [overview, setOverview] = useState<CacheOverview | null>(null);
  const [networkStatus, setNetworkStatus] = useState(
    infrastructure.getNetworkStatus()
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [unitAction, setUnitAction] = useState<UnitActionState | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const loadOverview = useCallback(async () => {
    try {
      const status = infrastructure.getNetworkStatus();
      if (isMounted.current) {
        setNetworkStatus(status);
      }
      const data = await offlineCache.getCacheOverview();
      if (isMounted.current) {
        setOverview(data);
        setErrorMessage(null);
      }
    } catch (error: any) {
      if (isMounted.current) {
        setErrorMessage(error?.message ?? 'Failed to load cache state');
      }
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    }
  }, [infrastructure, offlineCache]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useFocusEffect(
    useCallback(() => {
      loadOverview();
    }, [loadOverview])
  );

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadOverview();
  }, [loadOverview]);

  const handleSyncNow = useCallback(async () => {
    setIsSyncing(true);
    try {
      await content.syncNow();
      trigger('success');
    } catch (error: any) {
      setErrorMessage(error?.message ?? 'Sync failed');
    } finally {
      setIsSyncing(false);
      await loadOverview();
    }
  }, [content, loadOverview, trigger]);

  const handleClearAll = useCallback(async () => {
    setIsClearing(true);
    try {
      await offlineCache.clearAll();
      trigger('light');
    } catch (error: any) {
      setErrorMessage(error?.message ?? 'Failed to clear cache');
    } finally {
      setIsClearing(false);
      await loadOverview();
    }
  }, [loadOverview, offlineCache, trigger]);

  const handleDownloadFull = useCallback(
    async (unitId: string) => {
      setUnitAction({ unitId, action: 'download' });
      try {
        await content.requestUnitDownload(unitId);
        trigger('medium');
      } catch (error: any) {
        setErrorMessage(error?.message ?? 'Failed to queue download');
      } finally {
        setUnitAction(null);
        await loadOverview();
      }
    },
    [content, loadOverview, trigger]
  );

  const handleDowngrade = useCallback(
    async (unitId: string) => {
      setUnitAction({ unitId, action: 'downgrade' });
      try {
        await offlineCache.markUnitCacheMode(unitId, 'minimal');
        trigger('light');
      } catch (error: any) {
        setErrorMessage(error?.message ?? 'Failed to downgrade unit');
      } finally {
        setUnitAction(null);
        await loadOverview();
      }
    },
    [loadOverview, offlineCache, trigger]
  );

  const handleDeleteUnit = useCallback(
    async (unitId: string) => {
      setUnitAction({ unitId, action: 'delete' });
      try {
        await offlineCache.deleteUnit(unitId);
        trigger('light');
      } catch (error: any) {
        setErrorMessage(error?.message ?? 'Failed to delete unit');
      } finally {
        setUnitAction(null);
        await loadOverview();
      }
    },
    [loadOverview, offlineCache, trigger]
  );

  const formatLastSync = useCallback((timestamp: number | undefined | null) => {
    if (!timestamp) {
      return 'Never';
    }
    return new Date(timestamp).toLocaleString();
  }, []);

  const totalStorage = overview?.totalStorageBytes ?? 0;
  const syncStatus = overview?.syncStatus;
  const cachedUnits = overview?.units ?? [];

  const pendingWrites = syncStatus?.pendingWrites ?? 0;
  const lastSyncAttempt = syncStatus?.lastSyncAttempt ?? 0;
  const lastSyncResult = syncStatus?.lastSyncResult ?? 'idle';

  const formattedStorage = useMemo(() => formatBytes(totalStorage), [
    totalStorage,
  ]);

  const isOnline = Boolean(networkStatus?.isConnected);

  if (isLoading) {
    return (
      <SafeAreaView
        style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}
        testID="cache-management-screen"
      >
        <ActivityIndicator color={theme.colors.primary} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      testID="cache-management-screen"
    >
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            colors={[theme.colors.primary]}
            tintColor={theme.colors.primary}
          />
        }
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.topBar}>
          <Button
            title="Back"
            variant="secondary"
            size="small"
            onPress={() => navigation.goBack()}
            icon={<ArrowLeft size={16} color={theme.colors.primary} />}
            testID="cache-back-button"
          />
          <View style={styles.topBarTitles}>
            <Text variant="h1">Downloads</Text>
            <Text
              variant="secondary"
              color={theme.colors.textSecondary}
              testID="cache-summary-total-storage"
            >
              Storage used: {formattedStorage}
            </Text>
          </View>
        </View>

        <View style={styles.statusRow}>
          <View
            style={[
              styles.statusBadge,
              {
                backgroundColor: isOnline
                  ? theme.colors.success
                  : theme.colors.error,
              },
            ]}
            testID="cache-network-status"
          >
            {isOnline ? (
              <Cloud size={16} color={theme.colors.surface} />
            ) : (
              <CloudOff size={16} color={theme.colors.surface} />
            )}
            <Text
              variant="caption"
              color={theme.colors.surface}
              style={styles.badgeText}
            >
              {isOnline ? 'Online' : 'Offline'}
            </Text>
          </View>
          <View
            style={[styles.statusBadge, { backgroundColor: theme.colors.surface }]}
            testID="cache-pending-writes"
          >
            <HardDrive size={16} color={theme.colors.textSecondary} />
            <Text variant="caption" color={theme.colors.textSecondary}>
              Pending writes: {pendingWrites}
            </Text>
          </View>
        </View>

        <View
          style={[styles.summaryCard, { backgroundColor: theme.colors.surface }]}
        >
          <Text variant="title">Sync activity</Text>
          <Text variant="body">Last sync: {formatLastSync(lastSyncAttempt)}</Text>
          <Text
            variant="secondary"
            color={
              lastSyncResult === 'error'
                ? theme.colors.error
                : theme.colors.textSecondary
            }
          >
            Status: {lastSyncResult}
          </Text>
          {syncStatus?.lastSyncError ? (
            <Text
              variant="caption"
              color={theme.colors.error}
              testID="cache-last-error"
            >
              {syncStatus.lastSyncError}
            </Text>
          ) : null}
          <Text variant="caption" color={theme.colors.textSecondary}>
            Last pull: {formatLastSync(syncStatus?.lastPulledAt ?? null)}
          </Text>
          <View style={styles.summaryActions}>
            <Button
              title="Sync now"
              variant="primary"
              size="small"
              onPress={handleSyncNow}
              loading={isSyncing}
              icon={<RotateCcw size={16} color={theme.colors.surface} />}
              testID="cache-sync-button"
            />
            <Button
              title="Clear all"
              variant="destructive"
              size="small"
              onPress={handleClearAll}
              loading={isClearing}
              icon={<Trash2 size={16} color={theme.colors.surface} />}
              testID="cache-clear-all-button"
            />
          </View>
        </View>

        {errorMessage ? (
          <Text
            variant="body"
            color={theme.colors.error}
            style={styles.errorText}
            testID="cache-error-message"
          >
            {errorMessage}
          </Text>
        ) : null}

        {cachedUnits.length === 0 ? (
          <View style={styles.emptyState} testID="cache-empty-state">
            <Text variant="title">No cached units yet</Text>
            <Text variant="secondary" color={theme.colors.textSecondary}>
              Download units to make them available offline.
            </Text>
          </View>
        ) : (
          cachedUnits.map(unit => {
            const isDownloading =
              unitAction?.unitId === unit.id &&
              unitAction.action === 'download';
            const isDowngrading =
              unitAction?.unitId === unit.id &&
              unitAction.action === 'downgrade';
            const isDeleting =
              unitAction?.unitId === unit.id && unitAction.action === 'delete';

            return (
              <View
                key={unit.id}
                style={[styles.unitCard, { backgroundColor: theme.colors.surface }]}
                testID={`cache-unit-${unit.id}`}
              >
                <View style={styles.unitHeader}>
                  <Text variant="title" testID={`cache-unit-${unit.id}-title`}>
                    {unit.title}
                  </Text>
                  <Text
                    variant="caption"
                    color={theme.colors.textSecondary}
                    testID={`cache-unit-${unit.id}-mode`}
                  >
                    {unit.cacheMode === 'full' ? 'Full download' : 'Minimal cache'}
                  </Text>
                </View>
                <Text
                  variant="secondary"
                  color={theme.colors.textSecondary}
                  testID={`cache-unit-${unit.id}-status`}
                >
                  Download status: {unit.downloadStatus}
                </Text>
                <Text
                  variant="secondary"
                  color={theme.colors.textSecondary}
                  testID={`cache-unit-${unit.id}-storage`}
                >
                  Storage: {formatBytes(unit.storageBytes)}
                </Text>
                <Text variant="caption" color={theme.colors.textSecondary}>
                  Lessons cached: {unit.lessonCount} · Assets downloaded:{' '}
                  {unit.downloadedAssets}/{unit.assetCount}
                </Text>
                <View style={styles.unitActions}>
                  {unit.cacheMode === 'minimal' ? (
                    <Button
                      title="Download full unit"
                      variant="primary"
                      size="small"
                      onPress={() => handleDownloadFull(unit.id)}
                      loading={isDownloading}
                      disabled={!isOnline}
                      icon={<Download size={16} color={theme.colors.surface} />}
                      testID={`cache-unit-download-${unit.id}`}
                    />
                  ) : (
                    <Button
                      title="Downgrade to minimal"
                      variant="secondary"
                      size="small"
                      onPress={() => handleDowngrade(unit.id)}
                      loading={isDowngrading}
                      icon={<CloudOff size={16} color={theme.colors.primary} />}
                      testID={`cache-unit-downgrade-${unit.id}`}
                    />
                  )}
                  <Button
                    title="Delete"
                    variant="destructive"
                    size="small"
                    onPress={() => handleDeleteUnit(unit.id)}
                    loading={isDeleting}
                    icon={<Trash2 size={16} color={theme.colors.surface} />}
                    testID={`cache-unit-delete-${unit.id}`}
                  />
                </View>
              </View>
            );
          })
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function formatBytes(bytes: number): string {
  if (!bytes) {
    return '0 B';
  }
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const precision = value < 10 && unitIndex > 0 ? 1 : 0;
  return `${value.toFixed(precision)} ${units[unitIndex]}`;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    padding: 20,
    gap: 16,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  topBarTitles: {
    flex: 1,
    marginLeft: 16,
    gap: 4,
  },
  statusRow: {
    flexDirection: 'row',
    gap: 12,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    gap: 8,
  },
  badgeText: {
    marginLeft: 4,
  },
  summaryCard: {
    borderRadius: 16,
    padding: 16,
    gap: 6,
  },
  summaryActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  errorText: {
    marginTop: 4,
  },
  emptyState: {
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  unitCard: {
    borderRadius: 16,
    padding: 16,
    gap: 8,
  },
  unitHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  unitActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
});

export default CacheManagementScreen;
