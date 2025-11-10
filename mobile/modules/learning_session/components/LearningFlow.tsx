/**
 * LearningFlow Component - Session Orchestrator
 *
 * Orchestrates the learning session flow, managing exercise progression,
 * progress tracking, and session completion.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView } from 'react-native';
import { Button, Progress, useHaptics } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { useActiveLearningSession } from '../queries';
import { useLearningSessionStore } from '../store';
import MultipleChoice from './MultipleChoice';
import ShortAnswer from './ShortAnswer';
import type { MCQContentDTO, ShortAnswerContentDTO } from '../models';
import { catalogProvider } from '../../catalog/public';
import { usePodcastPlayer, usePodcastState } from '../../podcast_player/public';

interface LearningFlowProps {
  sessionId: string;
  onComplete: (results: any) => void;
  onBack: () => void;
  unitId?: string | null;
  hasPlayer?: boolean;
}

export default function LearningFlow({
  sessionId,
  onComplete,
  onBack,
  unitId: initialUnitId,
  hasPlayer = false,
}: LearningFlowProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);
  const haptics = useHaptics();
  const { loadTrack, play } = usePodcastPlayer();
  const { playlist, currentTrack, lessonIdSkippedFrom } = usePodcastState();

  // Session data and actions
  const {
    session,
    exercises,
    isLoading,
    isError,
    error,
    updateProgress,
    completeSession,
    isUpdatingProgress,
    isCompleting,
  } = useActiveLearningSession(sessionId);

  // Local session state (select only what we need to avoid re-renders)
  const currentExerciseIndex = useLearningSessionStore(
    s => s.currentExerciseIndex
  );
  const setCurrentSession = useLearningSessionStore(s => s.setCurrentSession);
  const setCurrentExercise = useLearningSessionStore(s => s.setCurrentExercise);
  const completeExercise = useLearningSessionStore(s => s.completeExercise);

  // Get completed exercises count from store (only count valid exercise types)
  const completedExercisesCount = useLearningSessionStore(
    s =>
      Object.values(s.exerciseStates).filter(
        (exerciseState: any) => exerciseState?.isCompleted
      ).length
  );

  // Initialize session in store
  useEffect(() => {
    const resolvedUnitId = session?.unitId ?? initialUnitId ?? null;
    setCurrentSession(sessionId, resolvedUnitId);
    return () => {
      // Don't reset session on unmount - user might navigate back
    };
  }, [sessionId, session?.unitId, initialUnitId, setCurrentSession]);

  // Current exercise data
  const currentExercise = useMemo(() => {
    if (!exercises || !Array.isArray(exercises)) return null;
    return exercises[currentExerciseIndex] || null;
  }, [exercises, currentExerciseIndex]);

  // Count only actual exercises (filter to valid exercise types)
  const actualExercisesCount = useMemo(() => {
    if (!exercises || !Array.isArray(exercises)) return 0;
    return exercises.filter(e =>
      ['mcq', 'short_answer', 'coding'].includes(e.type)
    ).length;
  }, [exercises]);

  const progress = useMemo(() => {
    if (actualExercisesCount === 0) return 0;
    // Progress is the percentage of completed exercises out of total actual exercises
    return Math.min(1, completedExercisesCount / actualExercisesCount);
  }, [actualExercisesCount, completedExercisesCount]);

  // Track whether the podcast transcript intro has been shown this session
  const [transcriptShown, setTranscriptShown] = useState(false);
  const [podcastTranscript, setPodcastTranscript] = useState<string | null>(
    null
  );

  // Fetch podcast transcript from lesson details (package-aligned)
  useEffect(() => {
    let isMounted = true;
    const fetchTranscript = async () => {
      try {
        if (!session?.lessonId) return;
        const catalog = catalogProvider();
        const detail = await catalog.getLessonDetail(session.lessonId);
        if (!isMounted) return;
        setPodcastTranscript(detail?.podcastTranscript ?? null);
      } catch (e) {
        console.warn('Failed to load podcast transcript:', e);
        if (isMounted) setPodcastTranscript(null);
      }
    };
    fetchTranscript();
    return () => {
      isMounted = false;
    };
  }, [session?.lessonId]);

  // Show podcast transcript first when session starts and no exercises completed yet
  const shouldShowTranscript = useMemo(() => {
    return (
      !!session &&
      currentExerciseIndex === 0 &&
      completedExercisesCount === 0 &&
      !transcriptShown &&
      !!podcastTranscript &&
      Array.isArray(exercises) &&
      exercises.length > 0
    );
  }, [
    session,
    currentExerciseIndex,
    completedExercisesCount,
    podcastTranscript,
    exercises,
    transcriptShown,
  ]);

  // Load lesson track when transcript is shown, but don't autoplay
  // (User must click play button to start podcast - no autoplay on navigation)
  useEffect(() => {
    console.log('[LearningFlow] 🔍 Effect triggered. State:', {
      hasPlaylist: !!playlist,
      sessionLessonId: session?.lessonId,
      shouldShowTranscript,
      currentTrackLessonId: currentTrack?.lessonId,
      lessonIdSkippedFrom,
    });

    if (!playlist || !session?.lessonId || !shouldShowTranscript) {
      console.log('[LearningFlow] ⏭️ Skipping: missing prerequisites');
      return;
    }

    // Don't auto-load the track if the user manually skipped away from this lesson
    if (lessonIdSkippedFrom === session.lessonId) {
      console.log(
        '[LearningFlow] 🚫 Skipping auto-load for lesson',
        session.lessonId,
        '(user skipped away from it)'
      );
      return;
    }

    // Don't interfere if audio is playing a completely different lesson (user skipped around)
    // Only load our track if:
    // 1. No current track, OR
    // 2. Current track is already this lesson, OR
    // 3. No lessonIdSkippedFrom set (normal state)
    if (
      currentTrack?.lessonId &&
      currentTrack.lessonId !== session.lessonId &&
      lessonIdSkippedFrom !== null
    ) {
      console.log(
        '[LearningFlow] 🎵 Audio is on different lesson, not interfering. Current:',
        currentTrack.lessonId,
        'This lesson:',
        session.lessonId
      );
      return;
    }

    const lessonTrack = playlist.tracks.find(
      track => track.lessonId === session.lessonId
    );
    if (!lessonTrack) {
      console.log(
        '[LearningFlow] ⚠️ No track found for lesson',
        session.lessonId
      );
      return;
    }
    if (currentTrack && currentTrack.lessonId === session.lessonId) {
      console.log(
        '[LearningFlow] ✅ Already on correct track for lesson',
        session.lessonId
      );
      return;
    }

    // Load the track but don't play it automatically
    // User can click the play button to start
    console.log('[LearningFlow] 📥 Loading track for lesson', session.lessonId);
    loadTrack(lessonTrack).catch(error => {
      console.warn('[LearningFlow] Failed to load lesson podcast track', error);
    });
  }, [
    playlist,
    session?.lessonId,
    shouldShowTranscript,
    loadTrack,
    currentTrack,
    lessonIdSkippedFrom,
  ]);

  // Handle exercise completion
  const handleExerciseComplete = async (exerciseResults: any) => {
    if (!currentExercise) return;

    try {
      // Only update store and server for actual exercises
      const validExerciseTypes = ['mcq', 'short_answer', 'coding'];
      if (validExerciseTypes.includes(currentExercise.type)) {
        // Update local store for actual exercises only
        completeExercise(
          currentExercise.id,
          currentExercise.type as 'mcq' | 'short_answer' | 'coding',
          exerciseResults.isCorrect,
          exerciseResults.userAnswer
        );

        // Update server progress
        await updateProgress({
          sessionId,
          exerciseId: currentExercise.id,
          exerciseType: currentExercise.type as
            | 'mcq'
            | 'short_answer'
            | 'coding',
          isCorrect: exerciseResults.isCorrect,
          userAnswer: exerciseResults.userAnswer,
          timeSpentSeconds: exerciseResults.timeSpent || 0,
        });
      }

      // Move to next exercise or complete session
      if (currentExerciseIndex < (exercises?.length || 0) - 1) {
        setCurrentExercise(currentExerciseIndex + 1);
      } else {
        // Session complete
        handleSessionComplete();
      }
    } catch (error) {
      console.error('Failed to update progress:', error);
      Alert.alert('Error', 'Failed to save your progress. Please try again.', [
        { text: 'OK' },
      ]);
    }
  };

  // Glossary is excluded from exercise flow; no skip needed

  // Handle session completion
  const handleSessionComplete = async () => {
    try {
      const results = await completeSession();
      onComplete(results);
    } catch (error) {
      console.error('Failed to complete session:', error);
      Alert.alert(
        'Error',
        'Failed to complete the session. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };

  // Handle playing lesson podcast
  const handlePlayLessonPodcast = (): void => {
    if (currentTrack && currentTrack.lessonId === session?.lessonId) {
      // Track is already loaded, just play it
      play().catch(error => {
        console.warn('[LearningFlow] Failed to play lesson podcast:', error);
        Alert.alert('Error', 'Failed to play podcast. Please try again.');
      });
    } else {
      // Find and load the lesson track
      const lessonTrack = playlist?.tracks.find(
        track => track.lessonId === session?.lessonId
      );
      if (!lessonTrack) {
        Alert.alert('Error', 'Podcast for this lesson is not available.');
        return;
      }
      loadTrack(lessonTrack)
        .then(() => play())
        .catch(error => {
          console.warn('[LearningFlow] Failed to play lesson podcast:', error);
          Alert.alert('Error', 'Failed to play podcast. Please try again.');
        });
    }
  };

  // Note: exercise tracking start is handled inside each UI element (e.g., DidacticSnippet)

  // Render current exercise
  const renderCurrentExercise = () => {
    if (!currentExercise) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>
            No exercises available for this session.
          </Text>
        </View>
      );
    }

    switch (currentExercise.type) {
      case 'mcq':
        return (
          <MultipleChoice
            question={currentExercise.content as MCQContentDTO}
            onComplete={handleExerciseComplete}
            isLoading={isUpdatingProgress}
          />
        );

      case 'short_answer':
        return (
          <ShortAnswer
            question={currentExercise.content as ShortAnswerContentDTO}
            onComplete={handleExerciseComplete}
            isLoading={isUpdatingProgress}
          />
        );

      default:
        return (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>
              Unknown exercise type: {currentExercise.type}
            </Text>
            <Button
              title="Skip"
              onPress={() => handleExerciseComplete({ isCorrect: true })}
            />
          </View>
        );
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading session...</Text>
      </View>
    );
  }

  // Error state
  if (isError) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorTitle}>Session Error</Text>
        <Text style={styles.errorText}>
          {error?.message || 'Failed to load learning session'}
        </Text>
        <Button
          title="Go Back"
          onPress={onBack}
          variant="secondary"
          style={styles.errorButton}
        />
      </View>
    );
  }

  return (
    <View
      style={[
        styles.container,
        hasPlayer ? styles.containerWithMini : undefined,
      ]}
    >
      {/* Header with progress */}
      <View style={styles.header}>
        <View style={styles.progressContainer}>
          <Button
            title="✕"
            onPress={() => {
              haptics.trigger('light');
              onBack();
            }}
            variant="secondary"
            size="small"
            style={styles.closeButton}
            testID="learning-flow-close-button"
          />
          <View style={styles.progressWrapper}>
            <Progress
              progress={progress * 100}
              style={styles.progressBar}
              size="large"
            />
          </View>
        </View>
      </View>

      {/* Didactic first, then exercises */}
      <View
        style={[
          styles.componentContainer,
          hasPlayer ? styles.componentContainerWithMini : undefined,
        ]}
      >
        {shouldShowTranscript && podcastTranscript && (
          <View style={styles.transcriptContainer}>
            <View style={styles.transcriptHeader}>
              <Text style={styles.transcriptLabel}>
                Lesson Podcast Transcript
              </Text>
              {session?.lessonTitle ? (
                <Text style={styles.transcriptTitle}>
                  {session.lessonTitle}
                </Text>
              ) : null}
            </View>
            <ScrollView
              style={styles.transcriptScroll}
              contentContainerStyle={styles.transcriptScrollContent}
              showsVerticalScrollIndicator={false}
            >
              <Text style={styles.transcriptText}>{podcastTranscript}</Text>
            </ScrollView>
            <View style={styles.transcriptButtonContainer}>
              <Button
                title="Play Lesson Podcast"
                onPress={handlePlayLessonPodcast}
                variant="secondary"
                size="medium"
                testID="learning-flow-play-podcast-button"
              />
              <Button
                title="Start Exercises"
                onPress={() => {
                  setTranscriptShown(true);
                  setCurrentExercise(0);
                  haptics.trigger('light');
                }}
                loading={isUpdatingProgress}
                disabled={isUpdatingProgress}
                variant="primary"
                size="medium"
                style={styles.transcriptContinueButton}
                testID="learning-flow-transcript-continue"
              />
            </View>
          </View>
        )}
        {!shouldShowTranscript && renderCurrentExercise()}
      </View>

      {/* Footer with session controls */}
      {isCompleting && (
        <View style={styles.completingOverlay}>
          <Text style={styles.completingText}>Completing session...</Text>
        </View>
      )}
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    containerWithMini: {
      paddingBottom: 0,
    },
    header: {
      paddingTop: theme.spacing?.sm || 8,
      paddingHorizontal: theme.spacing?.md || 12,
      paddingBottom: theme.spacing?.xs || 4,
      backgroundColor: theme.colors.background,
    },
    progressContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'flex-start',
      width: '100%',
    },
    closeButton: {
      width: 28,
      height: 28,
      borderRadius: 14,
      aspectRatio: 1,
      marginRight: theme.spacing?.sm || 8,
      paddingHorizontal: 0,
      paddingVertical: 0,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: theme.colors.border,
      borderWidth: 0,
    },
    progressText: {
      fontSize: 16,
      fontWeight: '400',
      color: theme.colors.text,
    },
    progressBar: {
      flex: 1,
      width: '100%',
      marginTop: 0,
    },
    progressWrapper: {
      flex: 1,
      justifyContent: 'center',
      paddingVertical: 6,
    },
    componentContainer: {
      flex: 1,
    },
    componentContainerWithMini: {
      paddingBottom: 48, // Match UnitDetailScreen padding for podcast player
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: theme.colors.background,
    },
    loadingText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      marginTop: theme.spacing?.md || 12,
    },
    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: theme.spacing?.lg || 16,
      backgroundColor: theme.colors.background,
    },
    errorTitle: {
      fontSize: 20,
      fontWeight: 'normal',
      color: theme.colors.error,
      marginBottom: theme.spacing?.md || 12,
      textAlign: 'center',
    },
    errorText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      textAlign: 'center',
      marginBottom: theme.spacing?.xl || 24,
      lineHeight: 22,
    },
    errorButton: {
      minWidth: 120,
    },
    emptyState: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: theme.spacing?.lg || 16,
    },
    emptyStateText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      textAlign: 'center',
      lineHeight: 22,
    },
    transcriptContainer: {
      flex: 1,
      backgroundColor: theme.colors.surface,
      borderRadius: theme.borderRadius?.lg || 16,
      padding: theme.spacing?.lg || 16,
      gap: theme.spacing?.md || 12,
      shadowColor: theme.colors.shadow || '#000000',
      shadowOpacity: 0.12,
      shadowRadius: 12,
      elevation: 3,
    },
    transcriptHeader: {
      gap: theme.spacing?.xs || 6,
    },
    transcriptLabel: {
      fontSize: 12,
      fontWeight: '600',
      textTransform: 'uppercase',
      color: theme.colors.textSecondary,
      letterSpacing: 1,
    },
    transcriptTitle: {
      fontSize: 20,
      fontWeight: '600',
      color: theme.colors.text,
    },
    transcriptScroll: {
      flex: 1,
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: theme.borderRadius?.md || 12,
      paddingHorizontal: theme.spacing?.md || 16,
      paddingVertical: theme.spacing?.sm || 12,
      backgroundColor: theme.colors.surfaceSubdued,
    },
    transcriptScrollContent: {
      paddingBottom: theme.spacing?.lg || 16,
    },
    transcriptText: {
      fontSize: 16,
      lineHeight: 24,
      color: theme.colors.text,
    },
    transcriptButtonContainer: {
      gap: theme.spacing?.sm || 12,
    },
    transcriptContinueButton: {
      marginTop: 0,
    },
    completingOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: `${theme.colors.text}80`,
      justifyContent: 'center',
      alignItems: 'center',
    },
    completingText: {
      fontSize: 18,
      fontWeight: '400',
      color: theme.colors.surface,
      textAlign: 'center',
    },
    restoreContainer: {
      position: 'absolute',
      left: theme.spacing?.lg || 16,
      right: theme.spacing?.lg || 16,
      bottom: theme.spacing?.lg || 16,
      alignItems: 'center',
    },
    restoreButton: {
      minWidth: 160,
    },
  });
