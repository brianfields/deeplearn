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

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  StyleSheet,
  Text,
  ActivityIndicator,
  SafeAreaView,
  Alert,
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
import { catalogProvider } from '../../catalog/public';
import { infrastructureProvider } from '../../infrastructure/public';
import { offlineCacheProvider } from '../../offline_cache/public';
import type { PodcastTrack } from '../../podcast_player/public';
import NetInfo from '@react-native-community/netinfo';
import { useAuth } from '../../user/public';
import { TeachingAssistantButton } from '../../learning_conversations/components/TeachingAssistantButton';
import { TeachingAssistantModal } from '../../learning_conversations/components/TeachingAssistantModal';
import {
  useStartTeachingAssistant,
  useSubmitTeachingAssistantQuestion,
  useTeachingAssistantSessionState,
} from '../../learning_conversations/queries';
import type {
  TeachingAssistantStateRequest,
  TeachingAssistantStartPayload,
} from '../../learning_conversations/models';

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

  const { user } = useAuth();

  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);
  const haptics = useHaptics();
  const infrastructure = React.useMemo(() => infrastructureProvider(), []);

  const apiBase = useMemo(() => {
    const base =
      (infrastructure as any).getApiBaseUrl?.() ||
      (infrastructure as any).getBaseUrl?.() ||
      '';
    return typeof base === 'string' ? base.replace(/\/$/, '') : '';
  }, [infrastructure]);

  // Session creation mutation
  const startSessionMutation = useStartSession();
  const { loadPlaylist, loadTrack, play, pause, autoplayEnabled } =
    usePodcastPlayer();
  const { currentTrack, playlist } = usePodcastState();
  const hasPlayer = Boolean(
    unitId && playlist?.unitId === unitId && (playlist?.tracks.length ?? 0) > 0
  );
  const [_isPlaylistLoading, setIsPlaylistLoading] = useState(false);

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

  const [isOnline, setIsOnline] = useState<boolean>(infrastructure.isOnline());

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOnline(state?.isConnected ?? false);
    });
    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, []);

  useEffect(() => {
    if (!unitId) {
      setError('Unit context is required to start this lesson');
    }
  }, [unitId]);

  useEffect(() => {
    if (!assistantConversationId || !unitId) {
      return;
    }
    const nextRequest: TeachingAssistantStateRequest = {
      conversationId: assistantConversationId,
      unitId,
      lessonId: lesson.id ?? null,
      sessionId: sessionId ?? null,
      userId: user ? String(user.id) : null,
    };

    setAssistantRequest(previous => {
      if (!previous) {
        return nextRequest;
      }
      const unchanged =
        previous.conversationId === nextRequest.conversationId &&
        previous.unitId === nextRequest.unitId &&
        previous.lessonId === nextRequest.lessonId &&
        previous.sessionId === nextRequest.sessionId &&
        previous.userId === nextRequest.userId;
      return unchanged ? previous : nextRequest;
    });
  }, [assistantConversationId, lesson.id, sessionId, unitId, user]);

  useEffect(() => {
    if (!unitId) {
      return;
    }
    if (playlist?.unitId === unitId && (playlist?.tracks.length ?? 0) > 0) {
      return;
    }

    let isMounted = true;
    setIsPlaylistLoading(true);

    const loadUnitPlaylist = async (): Promise<void> => {
      try {
        const catalog = catalogProvider();
        const detail = await catalog.getUnitDetail(unitId);
        if (!isMounted) {
          return;
        }

        // Resolve podcast URLs from offline cache if downloaded
        const offlineCache = offlineCacheProvider();
        const unitDetail = await offlineCache.getUnitDetail(unitId);
        const isDownloaded = Boolean(unitDetail);

        const resolveAssetUrl = async (
          assetId: string | null,
          fallbackUrl: string | null
        ): Promise<string | null> => {
          if (!assetId || !fallbackUrl) {
            return fallbackUrl;
          }

          if (isDownloaded) {
            try {
              const asset = await offlineCache.resolveAsset(assetId);
              if (asset?.localPath) {
                return asset.localPath;
              }
            } catch (error) {
              console.warn(
                '[LearningFlowScreen] Failed to resolve asset',
                assetId,
                error
              );
            }
          }

          // Fallback to remote URL (convert relative to absolute)
          if (fallbackUrl && !/^https?:\/\//i.test(fallbackUrl)) {
            const path = fallbackUrl.startsWith('/')
              ? fallbackUrl
              : `/${fallbackUrl}`;
            return `${apiBase}${path}`;
          }
          return fallbackUrl;
        };

        const tracks: PodcastTrack[] = [];

        // Intro podcast
        if (detail?.podcastAudioUrl) {
          const introPodcastUrl = await resolveAssetUrl(
            unitDetail?.assets.find(a => a.type === 'audio')?.id ?? null,
            detail.podcastAudioUrl
          );
          if (introPodcastUrl) {
            tracks.push({
              unitId: detail.id,
              title: 'Intro Podcast',
              audioUrl: introPodcastUrl,
              durationSeconds: detail.podcastDurationSeconds ?? 0,
              transcript: detail.podcastTranscript ?? null,
              lessonId: null,
              lessonIndex: null,
            });
          }
        }

        // Lesson podcasts
        if (detail) {
          for (const [index, lessonSummary] of detail.lessons.entries()) {
            if (!lessonSummary.podcastAudioUrl) {
              continue;
            }

            const lessonAssetId = `lesson-podcast-${lessonSummary.id}`;
            const resolvedLessonUrl = await resolveAssetUrl(
              lessonAssetId,
              lessonSummary.podcastAudioUrl
            );

            if (!resolvedLessonUrl) {
              continue;
            }

            const isCurrentLesson = lessonSummary.id === lesson.id;
            tracks.push({
              unitId: detail.id,
              title: `Lesson ${index + 1}: ${lessonSummary.title}`,
              audioUrl: resolvedLessonUrl,
              durationSeconds: lessonSummary.podcastDurationSeconds ?? 0,
              transcript: isCurrentLesson
                ? (lesson.podcastTranscript ?? null)
                : null,
              lessonId: lessonSummary.id,
              lessonIndex: index,
            });
          }
        }

        if (tracks.length === 0) {
          console.warn('[LearningFlowScreen] No podcast tracks for unit', {
            unitId,
          });
          return;
        }

        await loadPlaylist(unitId, tracks);
        const shouldLoadInitialTrack =
          !currentTrack || currentTrack.unitId !== unitId;
        if (shouldLoadInitialTrack) {
          await loadTrack(tracks[0]);
          if (autoplayEnabled) {
            await play();
          }
        }
      } catch (playlistError) {
        console.error(
          '[LearningFlowScreen] Failed to load podcast playlist',
          playlistError
        );
      } finally {
        if (isMounted) {
          setIsPlaylistLoading(false);
        }
      }
    };

    void loadUnitPlaylist();

    return () => {
      isMounted = false;
    };
  }, [
    unitId,
    playlist?.unitId,
    playlist?.tracks.length,
    loadPlaylist,
    currentTrack,
    loadTrack,
    play,
    autoplayEnabled,
    apiBase,
    lesson,
  ]);

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
          userId: user ? String(user.id) : undefined,
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

  const handleOpenAssistant = useCallback(() => {
    if (!unitId) {
      Alert.alert('Unavailable', 'Unit context is required to ask questions.');
      return;
    }
    if (!isOnline) {
      Alert.alert(
        'Offline',
        'Reconnect to the internet to chat with the teaching assistant.'
      );
      return;
    }

    const basePayload: TeachingAssistantStartPayload = {
      unitId,
      lessonId: lesson.id ?? null,
      sessionId,
      userId: user ? String(user.id) : null,
    };

    setAssistantOpen(true);

    if (assistantConversationId) {
      setAssistantRequest(prev => {
        if (!prev || prev.conversationId !== assistantConversationId) {
          return {
            conversationId: assistantConversationId,
            ...basePayload,
          };
        }
        return prev;
      });
      assistantSessionQuery.refetch();
      return;
    }

    startTeachingAssistant.mutate(basePayload, {
      onSuccess: state => {
        setAssistantConversationId(state.conversationId);
        setAssistantRequest({
          conversationId: state.conversationId,
          ...basePayload,
        });
      },
      onError: () => {
        setAssistantOpen(false);
      },
    });
  }, [
    assistantConversationId,
    isOnline,
    lesson.id,
    sessionId,
    assistantSessionQuery,
    startTeachingAssistant,
    unitId,
    user,
  ]);

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
        lessonId: lesson.id ?? null,
        sessionId,
        userId: user ? String(user.id) : null,
      });
    },
    [
      assistantConversationId,
      lesson.id,
      sessionId,
      submitTeachingAssistantQuestion,
      unitId,
      user,
    ]
  );

  const handleAssistantQuickReply = useCallback(
    (reply: string) => {
      handleAssistantSend(reply);
    },
    [handleAssistantSend]
  );

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
          userId: user ? String(user.id) : undefined,
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
    const assistantDisabled =
      !isOnline ||
      submitTeachingAssistantQuestion.isPending ||
      startTeachingAssistant.isPending;

    return (
      <>
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
          <View style={styles.assistantButtonWrapper} pointerEvents="box-none">
            <TeachingAssistantButton
              onPress={handleOpenAssistant}
              disabled={assistantDisabled}
            />
          </View>
        </SafeAreaView>
        <TeachingAssistantModal
          visible={isAssistantOpen}
          onClose={handleAssistantClose}
          messages={assistantMessages}
          suggestedQuickReplies={assistantQuickReplies}
          onSend={handleAssistantSend}
          onSelectReply={handleAssistantQuickReply}
          context={assistantContext ?? null}
          isLoading={isAssistantLoading}
          disabled={assistantDisabled}
        />
      </>
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
    assistantButtonWrapper: {
      position: 'absolute',
      bottom: 100,
      right: 16,
      zIndex: 1000,
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
