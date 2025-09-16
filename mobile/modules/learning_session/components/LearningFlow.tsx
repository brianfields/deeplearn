/**
 * LearningFlow Component - Session Orchestrator
 *
 * Orchestrates the learning session flow, managing component progression,
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

// Simple component to auto-skip glossary components
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
      <Text style={styles.glossarySkipText}>Loading next component...</Text>
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
    components,
    isLoading,
    isError,
    error,
    updateProgress,
    completeSession,
    isUpdatingProgress,
    isCompleting,
  } = useActiveLearningSession(sessionId);

  // Local session state (select only what we need to avoid re-renders)
  const currentComponentIndex = useLearningSessionStore(
    s => s.currentComponentIndex
  );
  const setCurrentSession = useLearningSessionStore(s => s.setCurrentSession);
  const setCurrentComponent = useLearningSessionStore(
    s => s.setCurrentComponent
  );
  const completeComponent = useLearningSessionStore(s => s.completeComponent);

  // Initialize session in store
  useEffect(() => {
    setCurrentSession(sessionId);
    return () => {
      // Don't reset session on unmount - user might navigate back
    };
  }, [sessionId, setCurrentSession]);

  // Current component data
  const currentComponent = useMemo(() => {
    if (!components || !Array.isArray(components)) return null;
    return components[currentComponentIndex] || null;
  }, [components, currentComponentIndex]);

  // Progress calculation
  const progress = useMemo(() => {
    if (!components || !Array.isArray(components)) return 0;
    return components.length > 0
      ? (currentComponentIndex + 1) / components.length
      : 0;
  }, [components, currentComponentIndex]);

  // Handle component completion
  const handleComponentComplete = async (componentResults: any) => {
    if (!currentComponent) return;

    try {
      // Update local store
      completeComponent(
        currentComponent.id,
        componentResults.isCorrect,
        componentResults.userAnswer
      );

      // Update server progress
      await updateProgress({
        sessionId,
        componentId: currentComponent.id,
        isCorrect: componentResults.isCorrect,
        userAnswer: componentResults.userAnswer,
        timeSpentSeconds: componentResults.timeSpent || 0,
      });

      // Move to next component or complete session
      if (currentComponentIndex < (components?.length || 0) - 1) {
        setCurrentComponent(currentComponentIndex + 1);
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

  // Note: component tracking start is handled inside each component (e.g., DidacticSnippet)

  // Render current component
  const renderCurrentComponent = () => {
    if (!currentComponent) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>
            No components available for this session.
          </Text>
        </View>
      );
    }

    switch (currentComponent.type) {
      case 'didactic_snippet':
        return (
          <DidacticSnippet
            snippet={currentComponent.content}
            onContinue={() => handleComponentComplete({ isCorrect: true })}
            isLoading={isUpdatingProgress}
          />
        );

      case 'mcq':
        return (
          <MultipleChoice
            question={currentComponent.content}
            onComplete={handleComponentComplete}
            isLoading={isUpdatingProgress}
          />
        );

      case 'glossary':
        // Skip glossary components - they weren't in the old flow
        return (
          <GlossarySkip
            onComplete={() => handleComponentComplete({ isCorrect: true })}
            styles={styles}
          />
        );

      default:
        return (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>
              Unknown component type: {currentComponent.type}
            </Text>
            <Button
              title="Skip"
              onPress={() => handleComponentComplete({ isCorrect: true })}
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
          <Text style={styles.progressText} testID="learning-progress">
            {currentComponentIndex + 1} of {components?.length || 0}
          </Text>
        </View>
        <Progress progress={progress} style={styles.progressBar} />
        {session?.lessonTitle && (
          <Text style={styles.lessonTitle}>{session.lessonTitle}</Text>
        )}
      </View>

      {/* Current component */}
      <View style={styles.componentContainer}>{renderCurrentComponent()}</View>

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
