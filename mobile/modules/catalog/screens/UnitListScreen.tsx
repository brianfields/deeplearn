/**
 * LessonListScreen - Updated to show Units
 *
 * Displays available units for browsing, with search and navigation to UnitDetail.
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  TextInput,
  TouchableOpacity,
  SectionList,
} from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { reducedMotion } from '../../ui_system/utils/motion';
import { animationTimings } from '../../ui_system/utils/animations';
import { HardDrive, Plus, Search } from 'lucide-react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { UnitCard } from '../components/UnitCard';
import {
  useUserUnitCollections,
  useRetryUnitCreation,
  useDismissUnit,
} from '../queries';
import type { Unit } from '../public';
import type { LearningStackParamList } from '../../../types';
import { uiSystemProvider, Text, useHaptics } from '../../ui_system/public';
import { useAuth, userIdentityProvider } from '../../user/public';
import { Button } from '../../ui_system/components/Button';
import { contentProvider } from '../../content/public';
import {
  offlineCacheProvider,
  type CacheOverview,
  type DownloadStatus,
} from '../../offline_cache/public';

type LessonListScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'LessonList'
>;

type UnitListItem = {
  unit: Unit;
  downloadStatus: DownloadStatus;
  storageBytes: number;
  assetCount: number;
  downloadedAssets: number;
};

type UnitSection = {
  kind: 'downloaded' | 'available';
  title: string;
  data: UnitListItem[];
  emptyMessage: string;
};

export function LessonListScreen() {
  const navigation = useNavigation<LessonListScreenNavigationProp>();
  const [searchQuery, setSearchQuery] = useState('');
  const { user, signOut } = useAuth();
  const identity = userIdentityProvider();
  const currentUserId = user?.id ?? 0;
  const {
    data: collections,
    isLoading,
    refetch,
  } = useUserUnitCollections(currentUserId, { includeGlobal: true });
  const retryUnitMutation = useRetryUnitCreation();
  const dismissUnitMutation = useDismissUnit();
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const content = useMemo(() => contentProvider(), []);
  const offlineCache = useMemo(() => offlineCacheProvider(), []);
  const [cacheOverview, setCacheOverview] = useState<CacheOverview | null>(
    null
  );
  const [isCacheLoading, setIsCacheLoading] = useState(true);
  const [pendingDownloadId, setPendingDownloadId] = useState<string | null>(
    null
  );
  const hasLoadedCacheRef = useRef(false);

  const allUnits = collections?.units ?? [];
  const totalUnits = allUnits.length;

  const loadCacheOverview = useCallback(
    async (options?: { showLoading?: boolean }) => {
      if (!hasLoadedCacheRef.current || options?.showLoading) {
        setIsCacheLoading(true);
      }
      try {
        const overview = await offlineCache.getCacheOverview();
        setCacheOverview(overview);
        hasLoadedCacheRef.current = true;
      } catch (error) {
        console.warn('[UnitListScreen] Failed to load cache overview:', error);
      } finally {
        setIsCacheLoading(false);
      }
    },
    [offlineCache]
  );

  useEffect(() => {
    loadCacheOverview({ showLoading: true });
  }, [loadCacheOverview]);

  useFocusEffect(
    useCallback(() => {
      loadCacheOverview();
    }, [loadCacheOverview])
  );

  useEffect(() => {
    const units = cacheOverview?.units ?? [];
    const hasActiveDownloads = units.some(
      unit =>
        unit.downloadStatus === 'pending' ||
        unit.downloadStatus === 'in_progress'
    );

    if (!hasActiveDownloads) {
      return;
    }

    const interval = setInterval(() => {
      loadCacheOverview();
    }, 2000);

    return () => clearInterval(interval);
  }, [cacheOverview, loadCacheOverview]);

  // Handle pull-to-refresh by forcing a full sync
  const handleRefresh = useCallback(async () => {
    try {
      await content.syncNow(); // Force full sync, ignoring cursor
      await Promise.all([refetch(), loadCacheOverview({ showLoading: true })]);
    } catch (error) {
      console.warn('[UnitListScreen] Sync failed on refresh:', error);
      // Still refetch to show cached data
      await Promise.all([refetch(), loadCacheOverview({ showLoading: true })]);
    }
  }, [content, loadCacheOverview, refetch]);

  const matchesSearch = (unit: Unit) =>
    !searchQuery.trim() ||
    unit.title.toLowerCase().includes(searchQuery.trim().toLowerCase());

  const filteredUnits = useMemo(
    () => allUnits.filter(matchesSearch),
    [allUnits, searchQuery]
  );

  const cacheMetricsById = useMemo(() => {
    const map = new Map<string, CacheOverview['units'][number]>();
    for (const unit of cacheOverview?.units ?? []) {
      map.set(unit.id, unit);
    }
    return map;
  }, [cacheOverview]);

  const partitionedUnits = useMemo(() => {
    const downloaded: UnitListItem[] = [];
    const available: UnitListItem[] = [];
    for (const unit of filteredUnits) {
      const metrics = cacheMetricsById.get(unit.id);
      const status =
        metrics?.downloadStatus ??
        unit.downloadStatus ??
        ('idle' as DownloadStatus);
      const item: UnitListItem = {
        unit,
        downloadStatus: status,
        storageBytes: metrics?.storageBytes ?? 0,
        assetCount: metrics?.assetCount ?? 0,
        downloadedAssets: metrics?.downloadedAssets ?? 0,
      };
      if (status === 'completed') {
        downloaded.push(item);
      } else {
        available.push(item);
      }
    }
    return { downloaded, available };
  }, [cacheMetricsById, filteredUnits]);

  const downloadedUnits = partitionedUnits.downloaded;
  const availableUnits = partitionedUnits.available;

  const sections: UnitSection[] = [
    {
      kind: 'downloaded',
      title: 'Your downloaded units',
      data: downloadedUnits,
      emptyMessage: searchQuery
        ? 'No downloaded units match your search.'
        : isCacheLoading
          ? 'Loading downloaded units...'
          : 'No units downloaded yet',
    },
    {
      kind: 'available',
      title: 'Available units',
      data: availableUnits,
      emptyMessage: searchQuery
        ? 'No available units match your search.'
        : 'No units available',
    },
  ];

  const hasResults = downloadedUnits.length > 0 || availableUnits.length > 0;
  const downloadedCount = downloadedUnits.length;

  const handleDownloadUnit = useCallback(
    async (unitId: string) => {
      setPendingDownloadId(unitId);
      try {
        await content.requestUnitDownload(unitId);
        haptics.trigger('medium');
        await Promise.all([refetch(), loadCacheOverview()]);
      } catch (error) {
        console.warn('[UnitListScreen] Failed to queue unit download:', error);
      } finally {
        setPendingDownloadId(null);
      }
    },
    [content, haptics, loadCacheOverview, refetch]
  );

  const handleUnitPress = useCallback(
    (unit: Unit) => {
      navigation.navigate('UnitDetail', { unitId: unit.id });
    },
    [navigation]
  );

  const handleCreateUnit = useCallback(() => {
    haptics.trigger('medium');
    navigation.navigate('LearningCoach');
  }, [navigation, haptics]);

  const handleOpenDownloads = useCallback(() => {
    haptics.trigger('light');
    navigation.navigate('CacheManagement');
  }, [navigation, haptics]);

  const handleRetryUnit = useCallback(
    (unitId: string) => {
      if (!currentUserId) {
        return;
      }
      retryUnitMutation.mutate(
        { unitId, ownerUserId: currentUserId },
        { onSuccess: () => refetch() }
      );
    },
    [retryUnitMutation, currentUserId, refetch]
  );

  const handleDismissUnit = useCallback(
    (unitId: string) => {
      if (!currentUserId) {
        return;
      }
      dismissUnitMutation.mutate(
        { unitId, ownerUserId: currentUserId },
        { onSuccess: () => refetch() }
      );
    },
    [dismissUnitMutation, currentUserId, refetch]
  );

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      {/* Header */}
      <View style={[styles.header, styles.headerRow]}>
        <View style={{ flex: 1 }}>
          <Text
            variant="h1"
            testID="units-title"
            style={{ fontWeight: 'normal' }}
          >
            Units
          </Text>
          <Text variant="secondary" color={theme.colors.textSecondary}>
            {totalUnits} available
          </Text>
        </View>
        <View style={styles.headerActions}>
          <Button
            title="Downloads"
            variant="secondary"
            size="small"
            onPress={handleOpenDownloads}
            testID="unit-list-cache-button"
            icon={<HardDrive size={16} color={theme.colors.primary} />}
          />
          <Button
            title="Sign out"
            variant="secondary"
            size="small"
            style={styles.headerActionSpacing}
            testID="unit-list-logout-button"
            onPress={async () => {
              haptics.trigger('light');
              await identity.clear();
              await signOut();
            }}
          />
        </View>
      </View>

      {/* Search and Create Button */}
      <View style={styles.searchContainer}>
        <View
          style={[
            styles.searchInputContainer,
            {
              backgroundColor: theme.colors.surface,
              borderWidth: StyleSheet.hairlineWidth,
              borderColor: isSearchFocused
                ? theme.colors.secondary
                : theme.colors.border,
              shadowOpacity: 0,
              elevation: 0,
              borderRadius: 20,
              minHeight: 44,
            },
          ]}
        >
          <Search
            size={20}
            color={theme.colors.textSecondary}
            style={styles.searchIcon}
          />
          <TextInput
            style={[styles.searchInput, { color: theme.colors.text }]}
            placeholder="Search units..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor={theme.colors.textSecondary}
            onFocus={() => setIsSearchFocused(true)}
            onBlur={() => setIsSearchFocused(false)}
            testID="search-input"
          />
        </View>
        <TouchableOpacity
          style={[
            styles.createButton,
            { backgroundColor: theme.colors.primary },
            ui.getDesignSystem().shadows.medium as any,
          ]}
          onPress={handleCreateUnit}
          testID="create-unit-button"
        >
          <Plus size={20} color={theme.colors.surface} />
        </TouchableOpacity>
      </View>

      {/* Unit Sections */}
      <SectionList<UnitListItem, UnitSection>
        sections={sections}
        keyExtractor={item => item.unit.id}
        renderItem={({ item, index, section }) => {
          const overallIndex =
            section.kind === 'available' ? downloadedCount + index : index;
          return (
            <Animated.View
              entering={
                reducedMotion.enabled
                  ? undefined
                  : FadeIn.duration(animationTimings.ui).delay(
                      overallIndex * animationTimings.stagger
                    )
              }
              style={styles.listItemContainer}
            >
              <UnitCard
                unit={item.unit}
                onPress={handleUnitPress}
                onRetry={handleRetryUnit}
                onDismiss={handleDismissUnit}
                index={overallIndex}
                downloadStatus={item.downloadStatus}
                storageBytes={item.storageBytes}
                downloadedAssets={item.downloadedAssets}
                assetCount={item.assetCount}
                onDownload={handleDownloadUnit}
                isDownloadActionPending={pendingDownloadId === item.unit.id}
              />
            </Animated.View>
          );
        }}
        renderSectionHeader={({ section }) => (
          <Text variant="title" style={styles.sectionHeader}>
            {section.title}
          </Text>
        )}
        renderSectionFooter={({ section }) =>
          section.data.length === 0 ? (
            <Text
              variant="secondary"
              color={theme.colors.textSecondary}
              style={styles.sectionFooter}
            >
              {section.emptyMessage}
            </Text>
          ) : null
        }
        contentContainerStyle={[
          styles.listContainer,
          !hasResults && styles.listContainerEmpty,
        ]}
        refreshing={isLoading}
        onRefresh={handleRefresh}
        ListFooterComponent={() =>
          hasResults ? null : (
            <View style={styles.emptyState}>
              <Search size={48} color={theme.colors.textSecondary} />
              <Text variant="title" style={{ marginTop: 16 }}>
                No Units Found
              </Text>
              <Text variant="body" color={theme.colors.textSecondary}>
                {searchQuery
                  ? 'Try adjusting your search'
                  : 'Pull down to refresh'}
              </Text>
            </View>
          )
        }
        stickySectionHeadersEnabled={false}
        showsVerticalScrollIndicator={false}
        removeClippedSubviews={true}
        maxToRenderPerBatch={10}
        windowSize={10}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingBottom: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerActionSpacing: {
    marginLeft: 8,
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 16,
    gap: 12,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  createButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listContainer: {
    padding: 20,
    paddingTop: 0,
  },
  listContainerEmpty: {
    flex: 1,
    justifyContent: 'center',
  },
  listItemContainer: {
    marginBottom: 0,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  sectionHeader: {
    marginTop: 24,
    marginBottom: 12,
  },
  sectionFooter: {
    marginBottom: 16,
  },
});
