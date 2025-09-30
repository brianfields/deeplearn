import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  FlatList,
  TouchableOpacity,
  Alert,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Audio } from 'expo-av';

import { useCatalogUnitDetail, useToggleUnitSharing } from '../queries';
import { UnitProgressView } from '../components/UnitProgress';
import type { LearningStackParamList } from '../../../types';
import {
  useUnitProgress as useUnitProgressLS,
  useNextLessonToResume,
} from '../../learning_session/queries';
import { catalogProvider } from '../public';
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
  const { data: unit } = useCatalogUnitDetail(unitId || '', {
    currentUserId: currentUserId ?? undefined,
  });
  const toggleSharing = useToggleUnitSharing();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const userKey = currentUserId ? String(currentUserId) : 'anonymous';
  const { data: progressLS } = useUnitProgressLS(userKey, unit?.id || '', {
    enabled: !!unit?.id,
    staleTime: 60 * 1000,
  });

  // Determine next lesson to resume within this unit
  const { data: nextLessonId } = useNextLessonToResume(
    userKey,
    unit?.id || '',
    {
      enabled: !!unit?.id,
      staleTime: 60 * 1000,
    }
  );

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
    if (!progressLS) return null;
    return {
      unitId: progressLS.unitId,
      completedLessons: progressLS.lessonsCompleted,
      totalLessons: progressLS.totalLessons,
      progressPercentage: Math.round(progressLS.progressPercentage),
    } as any;
  }, [progressLS]);

  const nextLessonTitle = useMemo(() => {
    if (!unit || !nextLessonId) return null;
    return unit.lessons.find(l => l.id === nextLessonId)?.title ?? null;
  }, [unit, nextLessonId]);

  const [podcastSound, setPodcastSound] = useState<Audio.Sound | null>(null);
  const [isLoadingPodcast, setIsLoadingPodcast] = useState(false);
  const [isPodcastPlaying, setIsPodcastPlaying] = useState(false);

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

  useEffect(() => {
    return () => {
      if (podcastSound) {
        podcastSound.unloadAsync().catch(() => {});
      }
    };
  }, [podcastSound]);

  useEffect(() => {
    if (podcastSound) {
      podcastSound.unloadAsync().catch(() => {});
      setPodcastSound(null);
      setIsPodcastPlaying(false);
    }
  }, [unit?.id]);

  const podcastDurationLabel = useMemo(() => {
    if (!unit?.podcastDurationSeconds) return null;
    const minutes = Math.floor(unit.podcastDurationSeconds / 60);
    const seconds = unit.podcastDurationSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }, [unit?.podcastDurationSeconds]);

  const handleTogglePodcast = useCallback(async () => {
    if (!unit?.hasPodcast || !podcastAudioUrl) {
      Alert.alert(
        'Podcast unavailable',
        'This unit does not have a podcast yet.'
      );
      return;
    }
    if (isLoadingPodcast) {
      return;
    }
    try {
      if (!podcastSound) {
        setIsLoadingPodcast(true);
        const { sound } = await Audio.Sound.createAsync(
          { uri: podcastAudioUrl },
          { shouldPlay: true }
        );
        sound.setOnPlaybackStatusUpdate(status => {
          if (!status.isLoaded) {
            return;
          }
          setIsPodcastPlaying(status.isPlaying);
          if (status.didJustFinish) {
            sound.setPositionAsync(0).catch(() => {});
            setIsPodcastPlaying(false);
          }
        });
        setPodcastSound(sound);
        setIsPodcastPlaying(true);
      } else {
        const status = await podcastSound.getStatusAsync();
        if (!status.isLoaded) {
          await podcastSound.unloadAsync();
          setPodcastSound(null);
          setIsPodcastPlaying(false);
          return;
        }
        if (status.isPlaying) {
          await podcastSound.pauseAsync();
          setIsPodcastPlaying(false);
        } else {
          await podcastSound.playAsync();
          setIsPodcastPlaying(true);
        }
      }
    } catch (error) {
      Alert.alert('Unable to play podcast', 'Please try again later.');
    } finally {
      setIsLoadingPodcast(false);
    }
  }, [podcastSound, unit, podcastAudioUrl, isLoadingPodcast]);

  const hasPodcast = Boolean(unit?.hasPodcast && podcastAudioUrl);

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

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
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
        <Text variant="secondary" color={theme.colors.textSecondary}>
          {unit.ownershipLabel}
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
        {unit.artImageDescription ? (
          <Text
            variant="secondary"
            color={theme.colors.textSecondary}
            style={{ marginTop: ui.getSpacing('sm') }}
          >
            {unit.artImageDescription}
          </Text>
        ) : null}
      </Box>

      <Box px="lg">
        <Card variant="default" style={{ margin: 0 }}>
          {nextLessonTitle && (
            <Box mb="md">
              <Text variant="secondary" color={theme.colors.textSecondary}>
                Resume next:
              </Text>
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

      {hasPodcast && (
        <Box px="lg" mt="md">
          <Card variant="outlined" style={{ margin: 0 }}>
            <Text variant="title" style={{ marginBottom: 8 }}>
              Unit Podcast
            </Text>
            {unit.podcastVoice && (
              <Text
                variant="secondary"
                color={theme.colors.textSecondary}
                style={{ marginBottom: 12 }}
              >
                Narrated in {unit.podcastVoice}
              </Text>
            )}
            <Button
              title={isPodcastPlaying ? 'Pause Podcast' : 'Play Podcast'}
              onPress={() => {
                haptics.trigger('light');
                handleTogglePodcast();
              }}
              variant="secondary"
              size="medium"
              fullWidth
              disabled={isLoadingPodcast}
              testID="podcast-toggle"
            />
            {isLoadingPodcast && (
              <View style={{ marginTop: 12, alignItems: 'center' }}>
                <ActivityIndicator color={theme.colors.primary} />
              </View>
            )}
            {podcastDurationLabel && (
              <Text
                variant="caption"
                color={theme.colors.textSecondary}
                style={{ marginTop: 12 }}
              >
                Duration: {podcastDurationLabel}
              </Text>
            )}
            {unit.podcastTranscript && (
              <Text variant="body" style={{ marginTop: 12 }}>
                {unit.podcastTranscript}
              </Text>
            )}
          </Card>
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

      <FlatList
        data={unit.lessons}
        keyExtractor={l => l.id}
        renderItem={({ item }) => (
          <Box px="lg" testID="lesson-card">
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
                  {progressLS && (
                    <Text variant="caption" color={theme.colors.accent}>
                      {Math.round(
                        progressLS.lessons.find(lp => lp.lessonId === item.id)
                          ?.progressPercentage || 0
                      )}
                      %
                    </Text>
                  )}
                  <Text variant="caption" color={theme.colors.textSecondary}>
                    {item.estimatedDuration} min
                  </Text>
                </View>
              </View>
            </Card>
          </Box>
        )}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  lessonRight: { alignItems: 'flex-end' },
  listContent: { paddingVertical: 8, paddingBottom: 24 },
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
