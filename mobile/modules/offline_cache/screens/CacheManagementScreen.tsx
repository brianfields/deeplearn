import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
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

  const cachedUnits = overview?.units ?? [];
  const downloadedUnits = useMemo(
    () => cachedUnits.filter(unit => unit.downloadStatus === 'completed'),
    [cachedUnits]
  );
  const availableUnits = useMemo(
    () => cachedUnits.filter(unit => unit.downloadStatus !== 'completed'),
    [cachedUnits]
  );
  const hasActiveDownloads = useMemo(
    () =>
      cachedUnits.some(
        unit =>
          unit.downloadStatus === 'pending' ||
          unit.downloadStatus === 'in_progress'
      ),
    [cachedUnits]
  );

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

  useEffect(() => {
    if (!hasActiveDownloads) {
      return;
    }

    const pollInterval = setInterval(() => {
      loadOverview();
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [hasActiveDownloads, loadOverview]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadOverview();
  }, [loadOverview]);

  const handleDownloadToggle = useCallback(
    async (unit: CacheOverview['units'][number]) => {
      const isDownloaded = unit.downloadStatus === 'completed';
      const isCancelable =
        unit.downloadStatus === 'pending' || unit.downloadStatus === 'in_progress';
      const action: UnitActionState['action'] =
        isDownloaded || isCancelable ? 'delete' : 'download';

      setUnitAction({ unitId: unit.id, action });

      try {
        if (action === 'delete') {
          await content.removeUnitDownload(unit.id);
          trigger('light');
        } else {
          await content.requestUnitDownload(unit.id);
          trigger('medium');
        }
      } catch (error: any) {
        console.error('[CacheManagement] Failed to process unit action:', {
          unitId: unit.id,
          action,
          error,
        });
      } finally {
        setUnitAction(null);
        await loadOverview();
      }
    },
    [content, loadOverview, trigger]
  );

  const isOnline = infrastructure.getNetworkStatus()?.isConnected ?? false;

  const renderUnitCard = useCallback(
    (unit: CacheOverview['units'][number], section: 'downloaded' | 'available') => {
      const isDownloaded = unit.downloadStatus === 'completed';
      const isPending = unit.downloadStatus === 'pending';
      const isInProgress = unit.downloadStatus === 'in_progress';
      const isFailed = unit.downloadStatus === 'failed';
      const isCancelable = isPending || isInProgress;
      const isActionTarget = unitAction?.unitId === unit.id;
      const isDeleting = isActionTarget && unitAction.action === 'delete';
      const isRequestingDownload =
        isActionTarget && unitAction.action === 'download';

      let statusContent: React.ReactNode = null;

      if (isPending || isInProgress) {
        const totalAssets = unit.assetCount ?? 0;
        const completedAssets = Math.min(unit.downloadedAssets ?? 0, totalAssets);
        const progressLabel = isPending
          ? 'Download queued...'
          : totalAssets > 0
            ? `Downloading... ${completedAssets}/${totalAssets} assets`
            : 'Downloading assets...';
        statusContent = (
          <View style={styles.progressRow} testID={`cache-unit-${unit.id}-progress`}>
            <ActivityIndicator size="small" color={theme.colors.primary} />
            <Text variant="caption" color={theme.colors.primary}>
              {progressLabel}
            </Text>
          </View>
        );
      } else if (isFailed) {
        statusContent = (
          <Text
            variant="caption"
            color={theme.colors.error}
            testID={`cache-unit-${unit.id}-progress`}
          >
            Download failed. Tap to retry.
          </Text>
        );
      } else if (isDownloaded) {
        const bytes = unit.storageBytes ?? 0;
        const label = bytes > 0 ? formatBytes(bytes) : 'Downloaded';
        statusContent = (
          <Text
            variant="caption"
            color={theme.colors.textSecondary}
            testID={`cache-unit-${unit.id}-storage`}
          >
            {label}
          </Text>
        );
      } else if (section === 'available') {
        statusContent = (
          <Text variant="caption" color={theme.colors.textSecondary}>
            Not downloaded
          </Text>
        );
      }

      const showSpinner = isDeleting || isRequestingDownload;
      const disableAction =
        showSpinner || (!isDownloaded && !isCancelable && !isOnline);
      const actionIcon = showSpinner ? (
        <ActivityIndicator size="small" color={theme.colors.textSecondary} />
      ) : isDownloaded || isCancelable ? (
        <Trash2 size={24} color={theme.colors.error} />
      ) : (
        <Download
          size={24}
          color={
            !isOnline && section === 'available'
              ? theme.colors.textSecondary
              : theme.colors.primary
          }
        />
      );

      return (
        <View
          key={unit.id}
          style={[styles.unitCard, { backgroundColor: theme.colors.surface }]}
          testID={`cache-unit-${unit.id}`}
        >
          <View style={styles.unitContent}>
            <View style={styles.unitInfo}>
              <Text variant="title" testID={`cache-unit-${unit.id}-title`}>
                {unit.title}
              </Text>
              {statusContent}
            </View>
            <TouchableOpacity
              onPress={() => handleDownloadToggle(unit)}
              disabled={disableAction}
              style={[
                styles.iconButton,
                !isOnline && !isDownloaded && !isCancelable && styles.iconButtonDisabled,
              ]}
              testID={`cache-unit-toggle-${unit.id}`}
            >
              {actionIcon}
            </TouchableOpacity>
          </View>
        </View>
      );
    },
    [handleDownloadToggle, isOnline, theme, unitAction]
  );

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

        <View style={styles.section} testID="cache-section-downloaded">
          <View style={styles.sectionHeader}>
            <Text variant="h2">Downloaded units</Text>
            <Text variant="secondary" color={theme.colors.textSecondary}>
              Fully available offline
            </Text>
          </View>
          {downloadedUnits.length === 0 ? (
            <View
              style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}
              testID="cache-empty-downloaded"
            >
              <Text variant="title">No units downloaded yet</Text>
              <Text variant="secondary" color={theme.colors.textSecondary}>
                Download units to make them available offline.
              </Text>
            </View>
          ) : (
            downloadedUnits.map(unit => renderUnitCard(unit, 'downloaded'))
          )}
        </View>

        <View style={styles.section} testID="cache-section-available">
          <View style={styles.sectionHeader}>
            <Text variant="h2">Available units</Text>
            <Text variant="secondary" color={theme.colors.textSecondary}>
              Download to use offline
            </Text>
          </View>
          {availableUnits.length === 0 ? (
            <View
              style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}
              testID="cache-empty-available"
            >
              <Text variant="title">No units available</Text>
              <Text variant="secondary" color={theme.colors.textSecondary}>
                Everything here is ready to learn.
              </Text>
            </View>
          ) : (
            availableUnits.map(unit => renderUnitCard(unit, 'available'))
          )}
        </View>
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
    gap: 24,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  title: {
    flex: 1,
  },
  section: {
    gap: 16,
  },
  sectionHeader: {
    gap: 4,
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
    gap: 12,
  },
  unitContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  unitInfo: {
    flex: 1,
    gap: 8,
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
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
