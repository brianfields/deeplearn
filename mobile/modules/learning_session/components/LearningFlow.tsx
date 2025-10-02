/**
 * LearningFlow Component - Session Orchestrator
 *
 * Orchestrates the learning session flow, managing exercise progression,
 * progress tracking, and session completion.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { Button, Progress, useHaptics } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { useActiveLearningSession } from '../queries';
import { useLearningSessionStore } from '../store';
import MiniLesson from './MiniLesson';
import MultipleChoice from './MultipleChoice';
import type { MCQContentDTO } from '../models';
import { catalogProvider } from '../../catalog/public';

interface LearningFlowProps {
  sessionId: string;
  onComplete: (results: any) => void;
  onBack: () => void;
  unitId?: string | null;
  hasPlayer?: boolean;
}

// Simple element to auto-skip glossary entries
// Glossary content is no longer part of exercise flow

export default function LearningFlow({
  sessionId,
  onComplete,
  onBack,
  unitId: _unitId,
  hasPlayer = false,
}: LearningFlowProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);
  const haptics = useHaptics();

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
    setCurrentSession(sessionId);
    return () => {
      // Don't reset session on unmount - user might navigate back
    };
  }, [sessionId, setCurrentSession]);

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

  // Track whether didactic has been shown this session locally
  const [didacticShown, setDidacticShown] = useState(false);
  const [didacticData, setDidacticData] = useState<any | null>(null);

  // Fetch mini lesson from lesson details (package-aligned)
  useEffect(() => {
    let isMounted = true;
    const fetchDidactic = async () => {
      try {
        if (!session?.lessonId) return;
        const catalog = catalogProvider();
        const detail = await catalog.getLessonDetail(session.lessonId);
        if (!isMounted) return;
        setDidacticData(detail?.miniLesson || null);
      } catch (e) {
        console.warn('Failed to load mini lesson:', e);
        if (isMounted) setDidacticData(null);
      }
    };
    fetchDidactic();
    return () => {
      isMounted = false;
    };
  }, [session?.lessonId]);

  // Show didactic snippet first when session starts and no exercises completed yet
  const shouldShowDidactic = useMemo(() => {
    return (
      !!session &&
      currentExerciseIndex === 0 &&
      completedExercisesCount === 0 &&
      !didacticShown &&
      !!didacticData &&
      Array.isArray(exercises) &&
      exercises.length > 0
    );
  }, [
    session,
    currentExerciseIndex,
    completedExercisesCount,
    didacticData,
    exercises,
    didacticShown,
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
        {shouldShowDidactic && (
          <MiniLesson
            snippet={{
              explanation: didacticData as string,
            }}
            lessonTitle={session?.lessonTitle}
            onContinue={() => {
              setDidacticShown(true);
              setCurrentExercise(0);
            }}
            isLoading={isUpdatingProgress}
          />
        )}
        {!shouldShowDidactic && renderCurrentExercise()}
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
    glossarySkipContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: theme.colors.background,
    },
    glossarySkipText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
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
