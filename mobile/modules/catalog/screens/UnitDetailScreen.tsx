import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useCatalogUnitDetail, useToggleUnitSharing } from '../queries';
import { UnitProgressView } from '../components/UnitProgress';
import type { LearningStackParamList } from '../../../types';
import {
  useUnitProgress as useUnitProgressLS,
  useNextLessonToResume,
} from '../../learning_session/queries';
import { catalogProvider } from '../public';
import { contentProvider } from '../../content/public';
import {
  ArtworkImage,
  Box,
  Card,
  Text,
  Button,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { useAuth } from '../../user/public';
import { infrastructureProvider } from '../../infrastructure/public';
import { PodcastPlayer, type PodcastTrack } from '../../podcast_player/public';
import { offlineCacheProvider, type DownloadStatus } from '../../offline_cache/public';
import { DownloadPrompt } from '../components/DownloadPrompt';

type UnitDetailScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'UnitDetail'
>;

export function UnitDetailScreen() {
  const route = useRoute<RouteProp<LearningStackParamList, 'UnitDetail'>>();
  const unitId = route.params?.unitId as string | undefined;
  const navigation = useNavigation<UnitDetailScreenNavigationProp>();
  const { user } = useAuth();
  const currentUserId = user?.id ?? null;
  const { data: unit, refetch } = useCatalogUnitDetail(unitId || '', {
    currentUserId: currentUserId ?? undefined,
  });
  const toggleSharing = useToggleUnitSharing();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const userKey = currentUserId ? String(currentUserId) : 'anonymous';
  const content = useMemo(() => contentProvider(), []);
  const offlineCache = useMemo(() => offlineCacheProvider(), []);
  const [isDownloadActionPending, setIsDownloadActionPending] = useState(false);
  const [isCancelPending, setIsCancelPending] = useState(false);
  const [unitMetrics, setUnitMetrics] = useState<{
    assetCount: number;
    downloadedAssets: number;
    storageBytes: number;
  }>({ assetCount: 0, downloadedAssets: 0, storageBytes: 0 });

  const downloadStatus: DownloadStatus = useMemo(() => {
    return (unit?.downloadStatus as DownloadStatus | undefined) ?? 'idle';
  }, [unit?.downloadStatus]);
  const isDownloaded = downloadStatus === 'completed';
  const isDownloadInProgress =
    downloadStatus === 'pending' || downloadStatus === 'in_progress';
  const isDownloadFailed = downloadStatus === 'failed';

  const { data: progressLS } = useUnitProgressLS(userKey, unit?.id || '', {
    enabled: !!unit?.id && isDownloaded,
    staleTime: 60 * 1000,
  });

  // Determine next lesson to resume within this unit
  const { data: nextLessonId } = useNextLessonToResume(
    userKey,
    unit?.id || '',
    {
      enabled: !!unit?.id && isDownloaded,
      staleTime: 60 * 1000,
    }
  );

  const loadUnitMetrics = useCallback(async () => {
    if (!unit?.id) {
      setUnitMetrics({ assetCount: 0, downloadedAssets: 0, storageBytes: 0 });
      return;
    }

    try {
      const overview = await offlineCache.getCacheOverview();
      const entry = overview.units.find(item => item.id === unit.id);
      if (entry) {
        setUnitMetrics({
          assetCount: entry.assetCount,
          downloadedAssets: entry.downloadedAssets,
          storageBytes: entry.storageBytes,
        });
      } else {
        setUnitMetrics({ assetCount: 0, downloadedAssets: 0, storageBytes: 0 });
      }
    } catch (error) {
      console.warn('[UnitDetailScreen] Failed to load unit metrics', {
        unitId: unit.id,
        error,
      });
    }
  }, [offlineCache, unit?.id]);

  useEffect(() => {
    loadUnitMetrics();
  }, [loadUnitMetrics]);

  useEffect(() => {
    if (!isDownloadInProgress) {
      return;
    }

    const interval = setInterval(() => {
      loadUnitMetrics();
    }, 2000);

    return () => clearInterval(interval);
  }, [isDownloadInProgress, loadUnitMetrics]);

  useEffect(() => {
    if (!isDownloadInProgress) {
      return;
    }

    if (
      unitMetrics.assetCount > 0 &&
      unitMetrics.downloadedAssets >= unitMetrics.assetCount
    ) {
      refetch();
    }
  }, [isDownloadInProgress, refetch, unitMetrics.assetCount, unitMetrics.downloadedAssets]);

  const handleShareToggle = (nextValue: boolean): void => {
    if (!unit || !unit.isOwnedByCurrentUser) {
      Alert.alert(
        'Sharing unavailable',
        'Only the unit owner can change sharing settings.'
      );
      return;
    }

    toggleSharing.mutate({
      unitId: unit.id,
      makeGlobal: nextValue,
      actingUserId: currentUserId ?? undefined,
    });
  };

  const isTogglingShare = toggleSharing.isPending;

  const ownershipDescription = unit
    ? unit.isOwnedByCurrentUser
      ? unit.isGlobal
        ? 'This unit is shared with all learners.'
        : 'Only you can access this unit right now.'
      : unit.isGlobal
        ? 'Shared by another learner for everyone to explore.'
        : 'Owned by another learner.'
    : null;

  // Map LS progress to Units progress view shape
  const overallProgress = useMemo(() => {
    if (!progressLS || !isDownloaded) return null;
    return {
      unitId: progressLS.unitId,
      completedLessons: progressLS.lessonsCompleted,
      totalLessons: progressLS.totalLessons,
      progressPercentage: Math.round(progressLS.progressPercentage),
    } as any;
  }, [isDownloaded, progressLS]);

  const nextLessonTitle = useMemo(() => {
    if (!unit || !nextLessonId || !isDownloaded) return null;
    return unit.lessons.find(l => l.id === nextLessonId)?.title ?? null;
  }, [isDownloaded, nextLessonId, unit]);

  // Resolve absolute podcast URL against API base if backend returned a relative path
  const infra = infrastructureProvider();
  const apiBase = useMemo(() => {
    // Prefer getApiBaseUrl if available; fallback to getBaseUrl
    // Ensure no trailing slash
    const base =
      (infra as any).getApiBaseUrl?.() || (infra as any).getBaseUrl?.() || '';
    return typeof base === 'string' ? base.replace(/\/$/, '') : '';
  }, [infra]);

  const podcastAudioUrl = useMemo(() => {
    const url = unit?.podcastAudioUrl || null;
    if (!url) return null;
    if (/^https?:\/\//i.test(url)) return url;
    const path = url.startsWith('/') ? url : `/${url}`;
    return `${apiBase}${path}`;
  }, [unit?.podcastAudioUrl, apiBase]);

  const hasPodcast = useMemo(
    () => Boolean(unit?.hasPodcast && podcastAudioUrl && isDownloaded),
    [isDownloaded, podcastAudioUrl, unit?.hasPodcast]
  );

  const podcastTrack = useMemo<PodcastTrack | null>(() => {
    if (!unit || !hasPodcast || !podcastAudioUrl || !isDownloaded) {
      return null;
    }
    return {
      unitId: unit.id,
      title: unit.title,
      audioUrl: podcastAudioUrl,
      durationSeconds: unit.podcastDurationSeconds ?? 0,
      transcript: unit.podcastTranscript ?? null,
    };
  }, [hasPodcast, podcastAudioUrl, isDownloaded, unit]);

  // Note: PodcastPlayer component now handles loadTrack, no need to do it here

  const handleLessonPress = async (lessonId: string): Promise<void> => {
    try {
      const catalog = catalogProvider();
      const detail = await catalog.getLessonDetail(lessonId);
      if (!detail) {
        Alert.alert('Lesson not found', 'Unable to open this lesson.');
        return;
      }
      navigation.navigate('LearningFlow', {
        lessonId: detail.id,
        lesson: detail,
      });
    } catch {
      Alert.alert('Unable to open lesson', 'Please try again.');
    }
  };

  const estimatedDownloadSize = useMemo(() => {
    if (unitMetrics.storageBytes > 0) {
      return unitMetrics.storageBytes;
    }
    if (unitMetrics.assetCount > 0) {
      return unitMetrics.assetCount * 5 * 1024 * 1024;
    }
    const lessonCount = unit?.lessonIds?.length ?? unit?.lessons?.length ?? 0;
    if (lessonCount > 0) {
      return lessonCount * 5 * 1024 * 1024;
    }
    return null;
  }, [unit?.lessonIds, unit?.lessons, unitMetrics.assetCount, unitMetrics.storageBytes]);

  const handleQueueDownload = useCallback(async () => {
    if (!unit) {
      return;
    }

    setIsDownloadActionPending(true);
    try {
      await content.requestUnitDownload(unit.id);
      haptics.trigger('medium');
      await Promise.all([refetch(), loadUnitMetrics()]);
    } catch (error) {
      console.warn('[UnitDetailScreen] Failed to queue unit download', {
        unitId: unit.id,
        error,
      });
      Alert.alert(
        'Download failed',
        'We were unable to start the download. Please try again.'
      );
    } finally {
      setIsDownloadActionPending(false);
    }
  }, [content, haptics, loadUnitMetrics, refetch, unit]);

  const confirmDownload = useCallback(() => {
    if (!unit) {
      return;
    }

    const sizeLabel = estimatedDownloadSize
      ? `(~${formatBytes(estimatedDownloadSize)})`
      : '';
    Alert.alert(
      'Download unit',
      `Download "${unit.title}"? ${sizeLabel}`.trim(),
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Download', onPress: handleQueueDownload },
      ]
    );
  }, [estimatedDownloadSize, handleQueueDownload, unit]);

  const handleCancelDownload = useCallback(async () => {
    if (!unit) {
      return;
    }

    setIsCancelPending(true);
    try {
      await offlineCache.deleteUnit(unit.id);
      await content.syncNow();
      await Promise.all([refetch(), loadUnitMetrics()]);
    } catch (error) {
      console.warn('[UnitDetailScreen] Failed to cancel download', {
        unitId: unit.id,
        error,
      });
      Alert.alert(
        'Cancel failed',
        'We could not cancel the download. Please try again.'
      );
    } finally {
      setIsCancelPending(false);
    }
  }, [content, loadUnitMetrics, offlineCache, refetch, unit]);

  if (!unit) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <Box p="lg">
          <Text variant="h1">Unit not found</Text>
        </Box>
      </SafeAreaView>
    );
  }

  const lessonCountForPrompt = unit?.lessonIds?.length ?? unit.lessons.length;

  if (!isDownloaded) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Box p="lg" pb="sm">
            <TouchableOpacity
              onPress={() => {
                haptics.trigger('light');
                navigation.goBack();
              }}
              accessibilityRole="button"
              accessibilityLabel="Go back"
              style={{ paddingVertical: 6, paddingRight: 12 }}
            >
              <Text variant="body" color={theme.colors.primary}>
                {'‹ Back'}
              </Text>
            </TouchableOpacity>
            <Text variant="h1" style={{ marginTop: 8, fontWeight: 'normal' }}>
              {unit.title}
            </Text>
          </Box>

          <Box px="lg" mb="lg">
            <ArtworkImage
              title={unit.title}
              imageUrl={unit.artImageUrl ?? undefined}
              description={unit.artImageDescription ?? undefined}
              variant="hero"
              testID="unit-hero-art"
            />
          </Box>

          <Box px="lg">
            <DownloadPrompt
              title={unit.title}
              description={unit.description}
              lessonCount={lessonCountForPrompt}
              estimatedSizeBytes={estimatedDownloadSize}
              downloadStatus={downloadStatus}
              downloadedAssets={unitMetrics.downloadedAssets}
              assetCount={unitMetrics.assetCount}
              onDownload={confirmDownload}
              onCancel={
                isDownloadInProgress
                  ? handleCancelDownload
                  : () => navigation.goBack()
              }
              isDownloadActionPending={isDownloadActionPending}
              isCancelPending={isCancelPending}
            />
          </Box>

          {isDownloadFailed ? (
            <Box px="lg" mt="md">
              <Card variant="outlined" style={{ margin: 0 }}>
                <Text variant="secondary" color={theme.colors.error}>
                  Something went wrong downloading this unit. Please retry.
                </Text>
              </Card>
            </Box>
          ) : null}
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Box p="lg" pb="sm">
          <TouchableOpacity
            onPress={() => {
              haptics.trigger('light');
              navigation.goBack();
            }}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            style={{ paddingVertical: 6, paddingRight: 12 }}
          >
            <Text variant="body" color={theme.colors.primary}>
              {'‹ Back'}
            </Text>
          </TouchableOpacity>
          <Text variant="h1" style={{ marginTop: 8, fontWeight: 'normal' }}>
            {unit.title}
          </Text>
        </Box>

        <Box px="lg" mb="lg">
          <ArtworkImage
            title={unit.title}
            imageUrl={unit.artImageUrl ?? undefined}
            description={unit.artImageDescription ?? undefined}
            variant="hero"
            testID="unit-hero-art"
          />
        </Box>

        <Box px="lg">
          <Card variant="default" style={{ margin: 0 }}>
            {nextLessonTitle && (
              <Box mb="md">
                <Text variant="title" style={{ fontWeight: 'normal' }}>
                  {nextLessonTitle}
                </Text>
              </Box>
            )}

            {overallProgress && (
              <Box mb="md">
                <UnitProgressView progress={overallProgress} />
              </Box>
            )}

            <Button
              title={nextLessonTitle ? 'Resume Lesson' : 'Start Learning'}
              onPress={() => {
                const next = unit.lessons[0]?.id;
                if (next) {
                  handleLessonPress(next);
                } else {
                  Alert.alert('No lessons', 'This unit has no lessons yet.');
                }
              }}
              variant="primary"
              size="large"
              fullWidth
              testID="primary-cta"
            />
          </Card>
        </Box>

        {ownershipDescription && !unit.isOwnedByCurrentUser && (
          <Box px="lg" mt="md">
            <Card variant="outlined" style={{ margin: 0 }}>
              <Text variant="body">{ownershipDescription}</Text>
            </Card>
          </Box>
        )}

        <Box px="lg" mt="lg">
          <Text variant="title" style={{ marginBottom: 8 }}>
            Lessons
          </Text>
        </Box>

        {unit.lessons.map(item => (
          <Box key={item.id} px="lg" testID="lesson-card">
            <Card
              variant="outlined"
              style={{ margin: 0, marginBottom: 12 }}
              onPress={() => {
                haptics.trigger('light');
                handleLessonPress(item.id);
              }}
            >
              <View style={styles.lessonRowInner}>
                <Text variant="body" style={{ flex: 1, marginRight: 12 }}>
                  {item.title}
                </Text>
                <View style={styles.lessonRight}></View>
              </View>
            </Card>
          </Box>
        ))}
        {unit.isOwnedByCurrentUser && (
          <Box px="lg" mt="md">
            <Card variant="outlined" style={{ margin: 0 }}>
              <View style={styles.sharingRow}>
                <Text variant="body" style={{ flex: 1 }}>
                  Share globally
                </Text>
                <Switch
                  value={unit.isGlobal}
                  onValueChange={handleShareToggle}
                  disabled={isTogglingShare}
                />
              </View>
              <Text variant="caption" color={theme.colors.textSecondary}>
                {unit.isGlobal
                  ? 'Learners across the platform can view this unit.'
                  : 'Toggle on to make this unit visible to everyone.'}
              </Text>
            </Card>
          </Box>
        )}
      </ScrollView>
      {hasPodcast && podcastTrack && (
        <PodcastPlayer
          track={podcastTrack}
          unitId={unit.id}
          artworkUrl={unit.artImageUrl ?? undefined}
          defaultExpanded={false}
        />
      )}
    </SafeAreaView>
  );
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return 'Unknown size';
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
  container: { flex: 1 },
  scrollView: { flex: 1 },
  scrollContent: { paddingBottom: 96 }, // Extra padding for podcast player
  lessonRight: { alignItems: 'flex-end' },
  lessonRowInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sharingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
});
