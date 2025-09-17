/**
 * LearningFlow Component - Session Orchestrator
 *
 * Orchestrates the learning session flow, managing exercise progression,
 * progress tracking, and session completion.
 */

import React, { useEffect, useMemo } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { Button, Progress } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { useActiveLearningSession } from '../queries';
import { useLearningSessionStore } from '../store';
import DidacticSnippet from './DidacticSnippet';
import MultipleChoice from './MultipleChoice';

interface LearningFlowProps {
  sessionId: string;
  onComplete: (results: any) => void;
  onBack: () => void;
}

// Simple element to auto-skip glossary entries
function GlossarySkip({
  onComplete,
  styles,
}: {
  onComplete: () => void;
  styles: any;
}) {
  useEffect(() => {
    // Auto-advance after a brief moment
    const timer = setTimeout(() => {
      onComplete();
    }, 100);

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <View style={styles.glossarySkipContainer}>
      <Text style={styles.glossarySkipText}>Loading next item...</Text>
    </View>
  );
}

export default function LearningFlow({
  sessionId,
  onComplete,
  onBack,
}: LearningFlowProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

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

  const skipGlossary = () => {
    // Advance without recording progress (glossary is not an exercise)
    if (exercises && currentExerciseIndex < exercises.length - 1) {
      setCurrentExercise(currentExerciseIndex + 1);
    } else {
      handleSessionComplete();
    }
  };

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
      case 'didactic_snippet':
        return (
          <DidacticSnippet
            snippet={currentExercise.content}
            onContinue={() => handleExerciseComplete({ isCorrect: true })}
            isLoading={isUpdatingProgress}
          />
        );

      case 'mcq':
        return (
          <MultipleChoice
            question={currentExercise.content}
            onComplete={handleExerciseComplete}
            isLoading={isUpdatingProgress}
          />
        );

      case 'glossary':
        // Skip glossary entries (not counted as exercises)
        return <GlossarySkip onComplete={skipGlossary} styles={styles} />;

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
    <View style={styles.container}>
      {/* Header with progress */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <Button
            title="← Back"
            onPress={onBack}
            variant="secondary"
            style={styles.backButton}
            testID="learning-flow-back-button"
          />
        </View>
        <Progress
          progress={progress * 100}
          showLabel={true}
          label={`${completedExercisesCount}/${actualExercisesCount} exercises`}
          style={styles.progressBar}
        />
        {session?.lessonTitle && (
          <Text style={styles.lessonTitle}>{session.lessonTitle}</Text>
        )}
      </View>

      {/* Current exercise */}
      <View style={styles.componentContainer}>{renderCurrentExercise()}</View>

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
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },
    header: {
      padding: theme.spacing?.lg || 16,
      paddingBottom: theme.spacing?.md || 12,
      backgroundColor: theme.colors?.surface || '#F8F9FA',
      borderBottomWidth: 1,
      borderBottomColor: theme.colors?.border || '#E0E0E0',
    },
    headerTop: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing?.md || 12,
    },
    backButton: {
      paddingHorizontal: theme.spacing?.md || 12,
      paddingVertical: theme.spacing?.sm || 8,
    },
    progressText: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors?.text || '#000000',
    },
    progressBar: {
      marginBottom: theme.spacing?.md || 12,
    },
    lessonTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: theme.colors?.text || '#000000',
      textAlign: 'center',
    },
    componentContainer: {
      flex: 1,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },
    loadingText: {
      fontSize: 16,
      color: theme.colors?.textSecondary || '#666666',
      marginTop: theme.spacing?.md || 12,
    },
    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: theme.spacing?.lg || 16,
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },
    errorTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors?.error || '#F44336',
      marginBottom: theme.spacing?.md || 12,
      textAlign: 'center',
    },
    errorText: {
      fontSize: 16,
      color: theme.colors?.textSecondary || '#666666',
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
      color: theme.colors?.textSecondary || '#666666',
      textAlign: 'center',
      lineHeight: 22,
    },
    glossarySkipContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },
    glossarySkipText: {
      fontSize: 16,
      color: theme.colors?.textSecondary || '#666666',
    },
    completingOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      justifyContent: 'center',
      alignItems: 'center',
    },
    completingText: {
      fontSize: 18,
      fontWeight: '600',
      color: '#FFFFFF',
      textAlign: 'center',
    },
  });
