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
import {
  View,
  StyleSheet,
  Text,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';

// Components
import LearningFlow from '../components/LearningFlow';
import { Button, useHaptics } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';

// Hooks
import { useStartSession } from '../queries';
import {
  usePodcastPlayer,
  PodcastPlayer,
  usePodcastState,
} from '../../podcast_player/public';

// Types
import type { LearningStackParamList } from '../../../types';
import type { SessionResults } from '../models';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<LearningStackParamList, 'LearningFlow'>;

export default function LearningFlowScreen({ navigation, route }: Props) {
  const { lesson, unitId: routeUnitId } = route.params;
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const unitId = routeUnitId;

  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);
  const haptics = useHaptics();

  // Session creation mutation
  const startSessionMutation = useStartSession();
  const { pause } = usePodcastPlayer();
  const { currentTrack } = usePodcastState();
  const hasPlayer = Boolean(unitId && currentTrack?.unitId === unitId);

  useEffect(() => {
    if (!unitId) {
      setError('Unit context is required to start this lesson');
    }
  }, [unitId]);

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
        if (!unitId) {
          throw new Error('Unit context is required to start this lesson');
        }
        const session = await startSessionMutation.mutateAsync({
          lessonId: lesson.id,
          unitId,
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
  }, [lesson.id, sessionId, unitId]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('blur', () => {
      if (currentTrack?.unitId && unitId && currentTrack.unitId === unitId) {
        pause().catch(() => {});
      }
    });
    return unsubscribe;
  }, [currentTrack?.unitId, navigation, pause, unitId]);

  const handleComplete = (results: SessionResults) => {
    // Navigate to results screen
    const resolvedUnitId = results.unitId ?? unitId;
    navigation.replace('Results', { results, unitId: resolvedUnitId });
  };

  const handleBack = () => {
    haptics.trigger('light');
    // Navigate back to lesson list
    navigation.goBack();
  };

  const handleRetry = () => {
    haptics.trigger('medium');
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
        if (!unitId) {
          throw new Error('Unit context is required to start this lesson');
        }
        const session = await startSessionMutation.mutateAsync({
          lessonId: lesson.id,
          unitId,
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
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors?.primary} />
        <Text style={styles.loadingText}>
          Starting your learning session...
        </Text>
        <View style={styles.loadingActions}>
          <Button
            title="Cancel"
            onPress={handleBack}
            variant="secondary"
            size="large"
            style={styles.backButton}
            testID="learning-start-cancel-button"
          />
        </View>
      </SafeAreaView>
    );
  }

  // Error state
  if (error) {
    return (
      <SafeAreaView style={styles.errorContainer}>
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
      </SafeAreaView>
    );
  }

  // Session created successfully - render learning flow
  if (sessionId) {
    return (
      <SafeAreaView style={styles.container}>
        <LearningFlow
          sessionId={sessionId}
          onComplete={handleComplete}
          onBack={handleBack}
          unitId={unitId}
          hasPlayer={hasPlayer}
        />
        {hasPlayer && currentTrack && unitId ? (
          <PodcastPlayer
            track={currentTrack}
            unitId={unitId}
            defaultExpanded={false}
          />
        ) : null}
      </SafeAreaView>
    );
  }

  // Fallback loading state
  return (
    <SafeAreaView style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={theme.colors?.primary} />
      <Text style={styles.loadingText}>Preparing session...</Text>
      <View style={styles.loadingActions}>
        <Button
          title="Cancel"
          onPress={handleBack}
          variant="secondary"
          size="large"
          style={styles.backButton}
          testID="learning-prep-cancel-button"
        />
      </View>
    </SafeAreaView>
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
      backgroundColor: theme.colors.background,
    },
    loadingText: {
      marginTop: 16,
      fontSize: 16,
      color: theme.colors.text,
      textAlign: 'center',
    },
    loadingActions: {
      marginTop: 20,
      width: '100%',
      paddingHorizontal: 20,
    },
    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
      backgroundColor: theme.colors.background,
    },
    errorTitle: {
      fontSize: 20,
      fontWeight: 'normal',
      color: theme.colors.error,
      marginBottom: 12,
      textAlign: 'center',
    },
    errorMessage: {
      fontSize: 16,
      color: theme.colors.text,
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
