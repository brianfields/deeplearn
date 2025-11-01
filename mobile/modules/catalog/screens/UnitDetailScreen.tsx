import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import {
  useCatalogUnitDetail,
  useToggleUnitSharing,
  useRemoveUnitFromMyUnits,
  useDownloadUnit,
  useRemoveUnitDownload,
} from '../queries';
import {
  UnitObjectiveSummaryList,
  UnitProgressView,
  type UnitObjectiveSummary,
} from '../components/UnitProgress';
import type { LearningStackParamList } from '../../../types';
import {
  useUnitProgress as useUnitProgressLS,
  useNextLessonToResume,
  useUnitLOProgress,
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
import {
  offlineCacheProvider,
  type DownloadStatus,
} from '../../offline_cache/public';
import { DownloadPrompt } from '../components/DownloadPrompt';
import type { LOProgressItem } from '../../learning_session/models';
import { Headphones } from 'lucide-react-native';
import { TeachingAssistantButton } from '../../learning_conversations/components/TeachingAssistantButton';
import { TeachingAssistantModal } from '../../learning_conversations/components/TeachingAssistantModal';
import {
  useStartTeachingAssistant,
  useSubmitTeachingAssistantQuestion,
  useTeachingAssistantSessionState,
} from '../../learning_conversations/queries';
import type { TeachingAssistantStateRequest } from '../../learning_conversations/models';

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
  const removeFromMyUnits = useRemoveUnitFromMyUnits();
  const downloadUnit = useDownloadUnit();
  const _removeDownload = useRemoveUnitDownload();
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

  // Teaching Assistant state
  const [isAssistantOpen, setAssistantOpen] = useState(false);
  const [assistantConversationId, setAssistantConversationId] = useState<
    string | null
  >(null);
  const [assistantRequest, setAssistantRequest] =
    useState<TeachingAssistantStateRequest | null>(null);

  const startTeachingAssistant = useStartTeachingAssistant();
  const submitTeachingAssistantQuestion = useSubmitTeachingAssistantQuestion();
  const assistantSessionQuery =
    useTeachingAssistantSessionState(assistantRequest);

  const assistantState =
    assistantSessionQuery.data ?? startTeachingAssistant.data ?? null;
  const assistantMessages = assistantState?.messages ?? [];
  const assistantQuickReplies = assistantState?.suggestedQuickReplies ?? [];
  const assistantContext = assistantState?.context ?? null;
  const isAssistantLoading =
    startTeachingAssistant.isPending ||
    submitTeachingAssistantQuestion.isPending ||
    assistantSessionQuery.isFetching;

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
  const unitLOProgressQuery = useUnitLOProgress(userKey, unit?.id || '', {
    enabled: Boolean(unit?.id && isDownloaded),
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
  }, [
    isDownloadInProgress,
    refetch,
    unitMetrics.assetCount,
    unitMetrics.downloadedAssets,
  ]);

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

  const loProgressById = useMemo(() => {
    const items = unitLOProgressQuery.data?.items ?? [];
    const map = new Map<string, LOProgressItem>();
    for (const item of items) {
      map.set(item.loId, item);
    }
    return map;
  }, [unitLOProgressQuery.data?.items]);

  const compactObjectives = useMemo<UnitObjectiveSummary[]>(() => {
    const objectives = unit?.learningObjectives ?? [];
    if (!Array.isArray(objectives) || objectives.length === 0) {
      return [];
    }

    return objectives.map(objective => {
      const progressItem = loProgressById.get(objective.id);
      return {
        id: objective.id,
        title: objective.title,
        status: progressItem?.status ?? 'not_started',
        progress: progressItem
          ? {
              exercisesCorrect: progressItem.exercisesCorrect,
              exercisesTotal: progressItem.exercisesTotal,
            }
          : null,
      };
    });
  }, [loProgressById, unit?.learningObjectives]);

  // Teaching Assistant handlers
  const handleOpenAssistant = useCallback(() => {
    if (!unitId) {
      Alert.alert('Unavailable', 'Unit context is required to ask questions.');
      return;
    }

    setAssistantOpen(true);

    if (assistantConversationId) {
      setAssistantRequest(prev => {
        if (!prev || prev.conversationId !== assistantConversationId) {
          return {
            conversationId: assistantConversationId,
            unitId,
            lessonId: null,
            sessionId: null,
            userId: user ? String(user.id) : null,
          };
        }
        return prev;
      });
      assistantSessionQuery.refetch();
      return;
    }

    startTeachingAssistant.mutate(
      {
        unitId,
        lessonId: null,
        sessionId: null,
        userId: user ? String(user.id) : null,
      },
      {
        onSuccess: state => {
          setAssistantConversationId(state.conversationId);
          setAssistantRequest({
            conversationId: state.conversationId,
            unitId,
            lessonId: null,
            sessionId: null,
            userId: user ? String(user.id) : null,
          });
        },
        onError: () => {
          setAssistantOpen(false);
        },
      }
    );
  }, [assistantConversationId, assistantSessionQuery, startTeachingAssistant, unitId, user]);

  const handleAssistantClose = useCallback(() => {
    setAssistantOpen(false);
  }, []);

  const handleAssistantSend = useCallback(
    (message: string) => {
      if (!assistantConversationId || !unitId) {
        return;
      }

      submitTeachingAssistantQuestion.mutate({
        conversationId: assistantConversationId,
        message,
        unitId,
        lessonId: null,
        sessionId: null,
        userId: user ? String(user.id) : null,
      });
    },
    [assistantConversationId, submitTeachingAssistantQuestion, unitId, user]
  );

  const handleAssistantQuickReply = useCallback(
    (reply: string) => {
      handleAssistantSend(reply);
    },
    [handleAssistantSend]
  );

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
    () => Boolean(unit?.hasPodcast && isDownloaded),
    [isDownloaded, unit?.hasPodcast]
  );

  // Resolve podcast audio asset to get local path when downloaded
  const [resolvedPodcastUrl, setResolvedPodcastUrl] = useState<string | null>(
    null
  );

  useEffect(() => {
    if (!unit || !isDownloaded || !unit.hasPodcast) {
      setResolvedPodcastUrl(null);
      return;
    }

    const resolvePodcastAsset = async () => {
      try {
        const offlineCache = offlineCacheProvider();
        const unitDetail = await offlineCache.getUnitDetail(unit.id);
        if (!unitDetail) {
          console.warn('[UnitDetail] No cached unit detail for podcast', {
            unitId: unit.id,
          });
          setResolvedPodcastUrl(podcastAudioUrl);
          return;
        }

        // Log all assets for diagnostics
        console.info('[UnitDetail] Unit detail assets', {
          unitId: unit.id,
          assetCount: unitDetail.assets.length,
          assets: unitDetail.assets.map(a => ({
            id: a.id,
            type: a.type,
            status: a.status,
            hasLocalPath: Boolean(a.localPath),
            localPath: a.localPath,
            remoteUri: a.remoteUri,
            downloadedAt: a.downloadedAt,
          })),
        });

        // Find the audio asset (podcast)
        const audioAsset = unitDetail.assets.find(
          asset => asset.type === 'audio'
        );

        if (audioAsset) {
          if (audioAsset.localPath) {
            console.info('[UnitDetail] Resolved podcast to local path', {
              unitId: unit.id,
              localPath: audioAsset.localPath,
            });
            setResolvedPodcastUrl(audioAsset.localPath);
          } else {
            // Asset exists but no local path - try to download it on-demand
            console.warn('[UnitDetail] Audio asset found without local path', {
              unitId: unit.id,
              assetId: audioAsset.id,
              assetStatus: audioAsset.status,
              remoteUri: audioAsset.remoteUri,
              downloadedAt: audioAsset.downloadedAt,
            });

            console.info('[UnitDetail] Attempting on-demand download', {
              unitId: unit.id,
              assetId: audioAsset.id,
            });
            const resolvedAsset = await offlineCache.resolveAsset(
              audioAsset.id
            );
            if (resolvedAsset?.localPath) {
              console.info('[UnitDetail] Downloaded podcast on-demand', {
                unitId: unit.id,
                localPath: resolvedAsset.localPath,
              });
              setResolvedPodcastUrl(resolvedAsset.localPath);
            } else {
              console.warn(
                '[UnitDetail] Failed to download podcast on-demand, using remote URL',
                {
                  unitId: unit.id,
                  resolvedAsset: resolvedAsset
                    ? {
                        status: resolvedAsset.status,
                        localPath: resolvedAsset.localPath,
                      }
                    : null,
                }
              );
              setResolvedPodcastUrl(podcastAudioUrl);
            }
          }
        } else {
          console.warn('[UnitDetail] No audio asset found in unit detail', {
            unitId: unit.id,
            availableAssetTypes: unitDetail.assets.map(a => a.type),
          });
          setResolvedPodcastUrl(podcastAudioUrl);
        }
      } catch (error) {
        console.error('[UnitDetail] Failed to resolve podcast asset', error);
        setResolvedPodcastUrl(podcastAudioUrl);
      }
    };

    resolvePodcastAsset();
  }, [unit, isDownloaded, podcastAudioUrl]);

  const podcastTrack = useMemo<PodcastTrack | null>(() => {
    if (!unit || !hasPodcast || !resolvedPodcastUrl || !isDownloaded) {
      return null;
    }

    return {
      unitId: unit.id,
      title: 'Intro Podcast',
      audioUrl: resolvedPodcastUrl,
      durationSeconds: unit.podcastDurationSeconds ?? 0,
      transcript: unit.podcastTranscript ?? null,
    };
  }, [hasPodcast, resolvedPodcastUrl, isDownloaded, unit]);

  // Note: PodcastPlayer component now handles loadTrack, no need to do it here

  const handleLessonPress = async (lessonId: string): Promise<void> => {
    try {
      const catalog = catalogProvider();
      const detail = await catalog.getLessonDetail(lessonId);
      if (!detail) {
        Alert.alert('Lesson not found', 'Unable to open this lesson.');
        return;
      }
      if (!unitId) {
        Alert.alert('Error', 'Unit context is required to start a lesson.');
        return;
      }
      navigation.navigate('LearningFlow', {
        lessonId: detail.id,
        lesson: detail,
        unitId,
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
  }, [
    unit?.lessonIds,
    unit?.lessons,
    unitMetrics.assetCount,
    unitMetrics.storageBytes,
  ]);

  const handleQueueDownload = useCallback(async () => {
    if (!unit) {
      return;
    }

    setIsDownloadActionPending(true);
    try {
      await downloadUnit.mutateAsync({ unitId: unit.id });
      haptics.trigger('medium');
      await loadUnitMetrics();
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
  }, [downloadUnit, haptics, loadUnitMetrics, unit]);

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

  const handleRemoveFromMyUnits = useCallback(() => {
    if (!unit || !currentUserId) {
      return;
    }

    Alert.alert(
      'Remove from My Units',
      `Remove "${unit.title}" from your collection?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            haptics.trigger('medium');
            removeFromMyUnits.mutate(
              { userId: currentUserId, unitId: unit.id },
              {
                onSuccess: () => {
                  Alert.alert('Removed', 'Unit removed from your collection.', [
                    {
                      text: 'OK',
                      onPress: () => navigation.navigate('LessonList'),
                    },
                  ]);
                },
                onError: error => {
                  console.error(
                    '[UnitDetailScreen] Failed to remove from My Units',
                    error
                  );
                  Alert.alert(
                    'Remove failed',
                    'We could not remove this unit. Please try again.'
                  );
                },
              }
            );
          },
        },
      ]
    );
  }, [currentUserId, haptics, navigation, removeFromMyUnits, unit]);

  const handleDeleteDownload = useCallback(() => {
    if (!unit) {
      return;
    }

    const sizeLabel = unitMetrics.storageBytes
      ? ` (${formatBytes(unitMetrics.storageBytes)})`
      : '';
    Alert.alert(
      'Delete Download',
      `Delete downloaded content for "${unit.title}"?${sizeLabel}\n\nYou'll need to download it again to access lessons offline.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            haptics.trigger('medium');
            try {
              await offlineCache.deleteUnit(unit.id);
              await content.syncNow();
              await Promise.all([refetch(), loadUnitMetrics()]);
              navigation.navigate('LessonList');
            } catch (error) {
              console.error(
                '[UnitDetailScreen] Failed to delete download',
                error
              );
              Alert.alert(
                'Delete failed',
                'We could not delete the download. Please try again.'
              );
            }
          },
        },
      ]
    );
  }, [
    content,
    haptics,
    loadUnitMetrics,
    navigation,
    offlineCache,
    refetch,
    unit,
    unitMetrics.storageBytes,
  ]);

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

  const showLoSection = compactObjectives.length > 0;

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
                navigation.navigate('LessonList');
              }}
              accessibilityRole="button"
              accessibilityLabel="Go to unit list"
              style={{ paddingVertical: 6, paddingRight: 12 }}
            >
              <Text variant="body" color={theme.colors.primary}>
                {'‹ Units'}
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
                  : () => navigation.navigate('LessonList')
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

          {!unit.isOwnedByCurrentUser && unit.isGlobal && currentUserId && (
            <Box px="lg" mt="lg">
              <Button
                title="Remove from My Units"
                variant="secondary"
                size="medium"
                fullWidth
                onPress={handleRemoveFromMyUnits}
                disabled={removeFromMyUnits.isPending}
                testID="remove-from-my-units-prompt"
              />
            </Box>
          )}
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
              navigation.navigate('LessonList');
            }}
            accessibilityRole="button"
            accessibilityLabel="Go to unit list"
            style={{ paddingVertical: 6, paddingRight: 12 }}
          >
            <Text variant="body" color={theme.colors.primary}>
              {'‹ Units'}
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

        {showLoSection ? (
          <>
            <Box px="lg" mt="lg">
              <Button
                title="Ask Questions About This Unit"
                onPress={handleOpenAssistant}
                variant="secondary"
                size="large"
                fullWidth
                testID="unit-ask-questions-button"
              />
            </Box>
            <Box px="lg" mt="md">
              <Card variant="outlined" style={styles.loCard}>
                <Text
                  variant="title"
                  style={[styles.loSectionTitle, { color: theme.colors.text }]}
                >
                  Learning Objectives
                </Text>
                {unitLOProgressQuery.isLoading ? (
                  <View style={styles.loLoadingRow}>
                    <ActivityIndicator
                      color={theme.colors.primary}
                      size="small"
                    />
                    <Text
                      style={[
                        styles.loLoadingText,
                        { color: theme.colors.textSecondary },
                      ]}
                    >
                      Updating progress…
                    </Text>
                  </View>
                ) : null}
                <UnitObjectiveSummaryList
                  objectives={compactObjectives}
                  testIDPrefix="unit-lo-compact"
                />
                <Button
                  title="View Detailed Progress"
                  variant="secondary"
                  onPress={() => {
                    if (!unit?.id) {
                      return;
                    }
                    navigation.navigate('UnitLODetail', {
                      unitId: unit.id,
                      unitTitle: unit.title,
                    });
                  }}
                  style={styles.loDetailButton}
                  testID="view-detailed-progress"
                />
              </Card>
            </Box>
          </>
        ) : null}

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
                <View style={styles.lessonRight}>
                  {item.hasPodcast ? (
                    <Headphones
                      size={18}
                      color={theme.colors.textSecondary}
                      accessibilityLabel="Lesson podcast available"
                    />
                  ) : null}
                </View>
              </View>
            </Card>
          </Box>
        ))}

        {!unit.isOwnedByCurrentUser && unit.isGlobal && currentUserId && (
          <Box px="lg" mt="lg">
            <Button
              title="Remove from My Units"
              variant="secondary"
              size="medium"
              fullWidth
              onPress={handleRemoveFromMyUnits}
              disabled={removeFromMyUnits.isPending}
              testID="remove-from-my-units"
            />
          </Box>
        )}

        {isDownloaded && (
          <Box px="lg" mt="md">
            <Button
              title={`Delete Download${unitMetrics.storageBytes ? ` (${formatBytes(unitMetrics.storageBytes)})` : ''}`}
              variant="secondary"
              size="medium"
              fullWidth
              onPress={handleDeleteDownload}
              testID="delete-download-button"
            />
          </Box>
        )}

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
        <Fragment>
          <Box px="lg" mb="xs" mt="md">
            <Text
              variant="caption"
              color={theme.colors.textSecondary}
              accessibilityRole="text"
            >
              Intro Podcast
            </Text>
          </Box>
          <PodcastPlayer
            track={podcastTrack}
            unitId={unit.id}
            artworkUrl={unit.artImageUrl ?? undefined}
            defaultExpanded={false}
          />
        </Fragment>
      )}
      <TeachingAssistantModal
        visible={isAssistantOpen}
        messages={assistantMessages}
        suggestedQuickReplies={assistantQuickReplies}
        onSend={handleAssistantSend}
        onSelectReply={handleAssistantQuickReply}
        context={assistantContext}
        isLoading={isAssistantLoading}
        onClose={handleAssistantClose}
      />
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
  loCard: { margin: 0 },
  loSectionTitle: { marginBottom: 12 },
  loLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  loLoadingText: {
    fontSize: 14,
    marginLeft: 8,
  },
  loDetailButton: {
    marginTop: 16,
  },
  lessonRight: { alignItems: 'flex-end', minWidth: 24 },
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
