/**
 * LearningFlowScreen - Navigation Wrapper for Learning Sessions
 *
 * This screen serves as the navigation layer for individual learning sessions.
 * It creates a new learning session and manages the learning flow lifecycle.
 *
 * NAVIGATION ARCHITECTURE ROLE:
 * - Entry point from the lesson selection (LessonListScreen)
 * - Receives lesson data via navigation route parameters
 * - Creates a new learning session for the lesson
 * - Manages navigation transitions to/from learning sessions
 * - Handles completion navigation to ResultsScreen
 *
 * RESPONSIBILITY SEPARATION:
 * - Screen-level: Navigation, route handling, session creation, screen lifecycle
 * - Component-level: Learning logic, progress tracking, user interactions
 *
 * NAVIGATION FLOW:
 * LessonListScreen → LearningFlowScreen → ResultsScreen
 *                ↗ (via route params)   ↗ (via completion)
 *
 * KEY FUNCTIONS:
 * - Extracts lesson data from navigation route parameters
 * - Creates a new learning session for the lesson
 * - Provides navigation callbacks to LearningFlow component
 * - Handles completion by navigating to ResultsScreen with results
 * - Manages back navigation to lesson list
 *
 * INTEGRATION POINTS:
 * - Receives LessonDetail from route.params
 * - Creates LearningSession via backend API
 * - Passes LearningResults to ResultsScreen
 * - Coordinates with React Navigation stack
 */

import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Text, ActivityIndicator } from 'react-native';

// Components
import LearningFlow from '../components/LearningFlow';
import { Button } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';

// Hooks
import { useStartSession } from '../queries';

// Types
import type { LearningStackParamList } from '../../../types';
import type { SessionResults } from '../models';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<LearningStackParamList, 'LearningFlow'>;

export default function LearningFlowScreen({ navigation, route }: Props) {
  const { lesson } = route.params;
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

  // Session creation mutation
  const startSessionMutation = useStartSession();

  // Create session on mount
  useEffect(() => {
    // Guard against StrictMode double-invoke and re-entries
    const startedRef = (createSession as any).startedRef as
      | React.MutableRefObject<string | null>
      | undefined;
    if (!startedRef) {
      (createSession as any).startedRef = {
        current: null,
      } as React.MutableRefObject<string | null>;
    }
    const guardRef = (createSession as any)
      .startedRef as React.MutableRefObject<string | null>;

    if (
      guardRef.current === lesson.id ||
      sessionId ||
      startSessionMutation.isPending
    )
      return;
    guardRef.current = lesson.id;

    async function createSession() {
      try {
        setError(null);
        const session = await startSessionMutation.mutateAsync({
          lessonId: lesson.id,
          userId: 'anonymous', // TODO: Get from user context when available
        });
        setSessionId(session.id);
      } catch (err) {
        console.error('Failed to create learning session:', err);
        setError(
          err instanceof Error ? err.message : 'Failed to create session'
        );
        // allow retry
        guardRef.current = null;
      }
    }

    createSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson.id, sessionId]);

  const handleComplete = (results: SessionResults) => {
    // Navigate to results screen
    navigation.replace('Results', { results });
  };

  const handleBack = () => {
    // Navigate back to lesson list
    navigation.goBack();
  };

  const handleRetry = () => {
    setError(null);
    setSessionId(null);
    // Re-trigger session creation
    const createSession = async () => {
      // reset guard to allow retry
      const startedRef = (createSession as any).startedRef as
        | React.MutableRefObject<string | null>
        | undefined;
      if (startedRef) {
        startedRef.current = null;
      }
      try {
        const session = await startSessionMutation.mutateAsync({
          lessonId: lesson.id,
          userId: 'anonymous',
        });
        setSessionId(session.id);
      } catch (err) {
        console.error('Failed to create learning session:', err);
        setError(
          err instanceof Error ? err.message : 'Failed to create session'
        );
      }
    };
    createSession();
  };

  // Loading state while creating session
  if (startSessionMutation.isPending && !sessionId) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors?.primary} />
        <Text style={styles.loadingText}>
          Starting your learning session...
        </Text>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorTitle}>Unable to Start Session</Text>
        <Text style={styles.errorMessage}>{error}</Text>
        <View style={styles.errorActions}>
          <Button
            title="Try Again"
            onPress={handleRetry}
            variant="primary"
            style={styles.retryButton}
          />
          <Button
            title="Go Back"
            onPress={handleBack}
            variant="secondary"
            style={styles.backButton}
          />
        </View>
      </View>
    );
  }

  // Session created successfully - render learning flow
  if (sessionId) {
    return (
      <View style={styles.container}>
        <LearningFlow
          sessionId={sessionId}
          onComplete={handleComplete}
          onBack={handleBack}
        />
      </View>
    );
  }

  // Fallback loading state
  return (
    <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={theme.colors?.primary} />
      <Text style={styles.loadingText}>Preparing session...</Text>
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
      backgroundColor: theme.colors?.background || '#ffffff',
    },
    loadingText: {
      marginTop: 16,
      fontSize: 16,
      color: theme.colors?.text || '#333333',
      textAlign: 'center',
    },
    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
      backgroundColor: theme.colors?.background || '#ffffff',
    },
    errorTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors?.error || '#dc3545',
      marginBottom: 12,
      textAlign: 'center',
    },
    errorMessage: {
      fontSize: 16,
      color: theme.colors?.text || '#333333',
      textAlign: 'center',
      marginBottom: 24,
      lineHeight: 22,
    },
    errorActions: {
      flexDirection: 'row',
      gap: 12,
    },
    retryButton: {
      minWidth: 120,
    },
    backButton: {
      minWidth: 120,
    },
  });
