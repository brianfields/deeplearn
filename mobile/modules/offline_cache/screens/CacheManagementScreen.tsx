import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ArrowLeft, Download, Trash2 } from 'lucide-react-native';

import { offlineCacheProvider, type CacheOverview } from '../public';
import { contentProvider } from '../../content/public';
import { infrastructureProvider } from '../../infrastructure/public';
import { Button } from '../../ui_system/components/Button';
import { Text, uiSystemProvider, useHaptics } from '../../ui_system/public';
import type { LearningStackParamList } from '../../../types';

interface UnitActionState {
  unitId: string;
  action: 'download' | 'delete';
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
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [unitAction, setUnitAction] = useState<UnitActionState | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const loadOverview = useCallback(async () => {
    try {
      const data = await offlineCache.getCacheOverview();
      if (isMounted.current) {
        setOverview(data);
      }
    } catch (error: any) {
      console.error('[CacheManagement] Failed to load overview:', error);
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useFocusEffect(
    useCallback(() => {
      loadOverview();
    }, [loadOverview])
  );

  // Poll for updates when there are pending/in-progress downloads
  useEffect(() => {
    const hasActiveDownloads = cachedUnits.some(
      unit =>
        unit.downloadStatus === 'pending' ||
        unit.downloadStatus === 'in_progress'
    );

    if (!hasActiveDownloads) {
      return;
    }

    const pollInterval = setInterval(() => {
      loadOverview();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [cachedUnits, loadOverview]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadOverview();
  }, [loadOverview]);

  const handleDownloadToggle = useCallback(
    async (unitId: string, isDownloaded: boolean) => {
      if (isDownloaded) {
        // Delete the download
        setUnitAction({ unitId, action: 'delete' });
        try {
          await offlineCache.deleteUnit(unitId);
          trigger('light');
        } catch (error: any) {
          console.error('[CacheManagement] Failed to delete unit:', error);
        } finally {
          setUnitAction(null);
          await loadOverview();
        }
      } else {
        // Download the unit
        setUnitAction({ unitId, action: 'download' });
        try {
          await content.requestUnitDownload(unitId);
          trigger('medium');
        } catch (error: any) {
          console.error('[CacheManagement] Failed to queue download:', error);
        } finally {
          setUnitAction(null);
          // Reload to show updated status
          await loadOverview();
        }
      }
    },
    [content, loadOverview, offlineCache, trigger]
  );

  const cachedUnits = overview?.units ?? [];
  const isOnline = infrastructure.getNetworkStatus()?.isConnected ?? false;

  if (isLoading) {
    return (
      <SafeAreaView
        style={[
          styles.loadingContainer,
          { backgroundColor: theme.colors.background },
        ]}
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
          <Text variant="h1" style={styles.title}>
            Downloads
          </Text>
        </View>

        {cachedUnits.length === 0 ? (
          <View style={styles.emptyState} testID="cache-empty-state">
            <Text variant="title">No downloads yet</Text>
            <Text variant="secondary" color={theme.colors.textSecondary}>
              Download units to make them available offline.
            </Text>
          </View>
        ) : (
          cachedUnits.map(unit => {
            const isFullyDownloaded =
              unit.cacheMode === 'full' && unit.downloadStatus === 'completed';
            const isPending = unit.downloadStatus === 'pending';
            const isInProgress = unit.downloadStatus === 'in_progress';
            const isDownloading =
              (unitAction?.unitId === unit.id &&
                unitAction.action === 'download') ||
              isPending ||
              isInProgress;
            const isDeleting =
              unitAction?.unitId === unit.id && unitAction.action === 'delete';
            const isProcessing = isDownloading || isDeleting;

            // Show progress text for downloads
            let progressText: string | null = null;
            if (isPending) {
              progressText = 'Download queued...';
            } else if (isInProgress) {
              progressText = `Downloading... ${unit.downloadedAssets}/${unit.assetCount} assets`;
            }

            // Show storage size for completed downloads with assets
            const showStorage =
              isFullyDownloaded &&
              unit.downloadedAssets > 0 &&
              unit.storageBytes > 0;

            return (
              <View
                key={unit.id}
                style={[
                  styles.unitCard,
                  { backgroundColor: theme.colors.surface },
                ]}
                testID={`cache-unit-${unit.id}`}
              >
                <View style={styles.unitContent}>
                  <View style={styles.unitInfo}>
                    <Text
                      variant="title"
                      testID={`cache-unit-${unit.id}-title`}
                    >
                      {unit.title}
                    </Text>
                    {progressText ? (
                      <Text
                        variant="caption"
                        color={theme.colors.primary}
                        testID={`cache-unit-${unit.id}-progress`}
                      >
                        {progressText}
                      </Text>
                    ) : showStorage ? (
                      <Text
                        variant="caption"
                        color={theme.colors.textSecondary}
                        testID={`cache-unit-${unit.id}-storage`}
                      >
                        {formatBytes(unit.storageBytes)}
                      </Text>
                    ) : null}
                  </View>
                  <TouchableOpacity
                    onPress={() =>
                      handleDownloadToggle(unit.id, isFullyDownloaded)
                    }
                    disabled={isProcessing || !isOnline}
                    style={[
                      styles.iconButton,
                      !isOnline &&
                        !isFullyDownloaded &&
                        styles.iconButtonDisabled,
                    ]}
                    testID={`cache-unit-toggle-${unit.id}`}
                  >
                    {isProcessing ? (
                      <ActivityIndicator
                        size="small"
                        color={theme.colors.textSecondary}
                      />
                    ) : isFullyDownloaded ? (
                      <Trash2 size={24} color={theme.colors.error} />
                    ) : (
                      <Download
                        size={24}
                        color={
                          isOnline
                            ? theme.colors.primary
                            : theme.colors.textSecondary
                        }
                      />
                    )}
                  </TouchableOpacity>
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
    gap: 16,
  },
  title: {
    flex: 1,
  },
  emptyState: {
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    gap: 8,
    marginTop: 40,
  },
  unitCard: {
    borderRadius: 16,
    padding: 16,
  },
  unitContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  unitInfo: {
    flex: 1,
    gap: 4,
  },
  iconButton: {
    padding: 8,
    marginLeft: 16,
  },
  iconButtonDisabled: {
    opacity: 0.5,
  },
});

export default CacheManagementScreen;
