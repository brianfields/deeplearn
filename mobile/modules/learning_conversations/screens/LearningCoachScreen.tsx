import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  ActivityIndicator,
  Text,
  StyleSheet,
  Alert,
  Pressable,
  SafeAreaView,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useAuth } from '../../user/public';
import { uiSystemProvider } from '../../ui_system/public';
import { ConversationContainer } from '../components/ConversationContainer';
import { ConversationHeader } from '../components/ConversationHeader';
import { BriefCard } from '../components/BriefCard';
import {
  useAcceptBriefMutation,
  useLearnerTurnMutation,
  useLearningCoachSession,
  useAttachResourceMutation,
  useStartLearningCoachSession,
} from '../queries';
import type { LearningStackParamList } from '../../../types';
import { useCreateUnit } from '../../catalog/queries';
import { LearningCoachMessage } from '../models';
import { useRef } from 'react';
import { useUserResources } from '../../resource/queries';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

type ScreenProps = NativeStackScreenProps<
  LearningStackParamList,
  'LearningCoach'
>;

export function LearningCoachScreen({
  navigation,
  route,
}: ScreenProps): React.ReactElement {
  const { user } = useAuth();
  const [conversationId, setConversationId] = useState<string | null>(
    route.params?.conversationId ?? null
  );
  const [optimisticMessage, setOptimisticMessage] =
    useState<LearningCoachMessage | null>(null);
  const startSession = useStartLearningCoachSession();
  const learnerTurn = useLearnerTurnMutation();
  const acceptBrief = useAcceptBriefMutation();
  const attachResource = useAttachResourceMutation();
  const createUnit = useCreateUnit();
  const sessionQuery = useLearningCoachSession(conversationId);
  const [pendingResourceId, setPendingResourceId] = useState<string | null>(
    null
  );
  const attachingResourceRef = useRef<string | null>(null);
  const resourcesQuery = useUserResources(user?.id ?? null, {
    enabled: !!user?.id,
  });

  useEffect(() => {
    if (!conversationId && !startSession.isPending && !startSession.isSuccess) {
      startSession.mutate(
        {
          topic: route.params?.topic ?? null,
          userId: user ? String(user.id) : null,
        },
        {
          onSuccess: state => {
            setConversationId(state.conversationId);
          },
        }
      );
    }
  }, [conversationId, route.params?.topic, startSession, user]);

  useEffect(() => {
    if (!conversationId && startSession.isSuccess) {
      setConversationId(startSession.data.conversationId);
    }
  }, [conversationId, startSession.data, startSession.isSuccess]);

  const sessionState = sessionQuery.data ?? startSession.data ?? null;

  // Debug: Log session state changes
  useEffect(() => {
    if (sessionState) {
      console.log('[LearningCoach] Session state updated:', {
        conversationId: sessionState.conversationId,
        finalizedTopic: sessionState.finalizedTopic ? 'present' : 'null',
        unitTitle: sessionState.unitTitle,
        learningObjectives: sessionState.learningObjectives,
        suggestedLessonCount: sessionState.suggestedLessonCount,
        messageCount: sessionState.messages.length,
      });
    }
  }, [sessionState]);

  // Combine real messages with optimistic message
  const displayMessages = useMemo(() => {
    const realMessages = sessionState?.messages ?? [];
    if (optimisticMessage) {
      return [...realMessages, optimisticMessage];
    }
    return realMessages;
  }, [sessionState?.messages, optimisticMessage]);

  // Extract quick replies from the most recent assistant message
  const quickReplies = useMemo(() => {
    const messages = sessionState?.messages ?? [];
    const lastAssistantMessage = messages
      .slice()
      .reverse()
      .find(msg => msg.role === 'assistant');

    const replies = lastAssistantMessage?.metadata?.suggested_quick_replies;
    return Array.isArray(replies) ? replies : [];
  }, [sessionState?.messages]);

  const isCoachLoading = useMemo(() => {
    return (
      startSession.isPending ||
      learnerTurn.isPending ||
      attachResource.isPending ||
      sessionQuery.isFetching
    );
  }, [
    startSession.isPending,
    learnerTurn.isPending,
    attachResource.isPending,
    sessionQuery.isFetching,
  ]);

  const conversationResources = sessionState?.resources ?? [];
  const hasLearnerMessage = useMemo(() => {
    const messages = sessionState?.messages ?? [];
    const hasUserMessage = messages.some(message => message.role === 'user');
    const hasResources = conversationResources.length > 0;
    return hasUserMessage || hasResources;
  }, [sessionState?.messages, conversationResources.length]);

  const coverageStatus = useMemo(() => {
    const ids = sessionState?.uncoveredLearningObjectiveIds;
    if (ids === undefined) {
      return null;
    }
    if (ids === null) {
      return {
        label: 'No learner resources shared yet',
        variant: 'neutral' as const,
      };
    }
    if (ids.length === 0) {
      return {
        label: 'Learner resources cover all objectives',
        variant: 'success' as const,
      };
    }
    const count = ids.length;
    return {
      label: `Supplemental content needed for ${count} objective${
        count === 1 ? '' : 's'
      }`,
      variant: 'warning' as const,
    };
  }, [sessionState?.uncoveredLearningObjectiveIds]);

  const canAttachResource = Boolean(conversationId);
  const isProcessingResource =
    attachResource.isPending || pendingResourceId !== null;

  useEffect(() => {
    const selected = route.params?.attachResourceId;
    console.log('[LearningCoach] attachResourceId effect:', {
      selected,
      conversationId,
      hasSelected: !!selected,
      hasConversationId: !!conversationId,
    });
    if (!selected || !conversationId) {
      return;
    }
    console.log('[LearningCoach] Setting pendingResourceId:', selected);
    navigation.setParams({ attachResourceId: undefined });
    setPendingResourceId(selected);
  }, [conversationId, navigation, route.params?.attachResourceId]);

  useEffect(() => {
    console.log('[LearningCoach] pendingResourceId effect:', {
      pendingResourceId,
      conversationId,
      hasPending: !!pendingResourceId,
      hasConversationId: !!conversationId,
      attachingResourceRef: attachingResourceRef.current,
    });
    if (!pendingResourceId || !conversationId) {
      return;
    }
    // Prevent duplicate calls for the same resource
    if (attachingResourceRef.current === pendingResourceId) {
      console.log('[LearningCoach] Already attaching this resource, skipping');
      return;
    }

    attachingResourceRef.current = pendingResourceId;

    // Create optimistic message showing the resource is being shared
    const resource = resourcesQuery.data?.find(r => r.id === pendingResourceId);
    if (resource) {
      const resourceName =
        resource.filename || resource.sourceUrl || 'resource';
      const optimistic: LearningCoachMessage = {
        id: `optimistic-resource-${Date.now()}`,
        role: 'user',
        content: `[shared ${resourceName}]`,
        metadata: {},
        createdAt: new Date().toISOString(),
      };
      setOptimisticMessage(optimistic);
    }

    console.log('[LearningCoach] Calling attachResource.mutate:', {
      conversationId,
      resourceId: pendingResourceId,
      userId: user ? String(user.id) : null,
    });
    attachResource.mutate(
      {
        conversationId,
        resourceId: pendingResourceId,
        userId: user ? String(user.id) : null,
      },
      {
        onSuccess: () => {
          // Clear optimistic message when real message arrives
          setOptimisticMessage(null);
        },
        onError: error => {
          console.error('[LearningCoach] attachResource error:', error);
          // Clear optimistic message on error
          setOptimisticMessage(null);
          const message =
            error instanceof Error
              ? error.message
              : 'Unable to share that resource. Please try again.';
          Alert.alert('Resource not attached', message);
        },
        onSettled: () => {
          console.log('[LearningCoach] attachResource settled');
          setPendingResourceId(null);
          attachingResourceRef.current = null;
        },
      }
    );
  }, [
    conversationId,
    pendingResourceId,
    user,
    attachResource,
    resourcesQuery.data,
  ]);

  const handleSend = (message: string) => {
    if (!conversationId) {
      return;
    }

    // Create optimistic message
    const optimistic: LearningCoachMessage = {
      id: `optimistic-${Date.now()}`,
      role: 'user',
      content: message,
      metadata: {},
      createdAt: new Date().toISOString(),
    };
    setOptimisticMessage(optimistic);

    learnerTurn.mutate(
      {
        conversationId,
        message,
        userId: user ? String(user.id) : null,
      },
      {
        onSuccess: () => {
          setOptimisticMessage(null);
        },
        onError: () => {
          setOptimisticMessage(null);
        },
      }
    );
  };

  const handleQuickReply = (reply: string) => {
    handleSend(reply);
  };

  const handleAddResource = () => {
    if (!canAttachResource) {
      Alert.alert(
        'Almost ready',
        'Please wait for your coach to connect before sharing materials.'
      );
      return;
    }
    navigation.navigate('AddResource', {
      attachToConversation: true,
      conversationId: conversationId,
    });
  };

  const handleCreateUnit = (): void => {
    console.log('[LearningCoach] handleCreateUnit called', {
      conversationId,
      learnerDesires: sessionState?.learnerDesires,
      unitTitle: sessionState?.unitTitle,
      learningObjectives: sessionState?.learningObjectives,
      suggestedLessonCount: sessionState?.suggestedLessonCount,
    });

    // Guard: Require all fields that coach should have finalized
    if (
      !conversationId ||
      !sessionState?.learnerDesires ||
      !sessionState?.unitTitle ||
      !sessionState?.learningObjectives ||
      !sessionState?.suggestedLessonCount
    ) {
      console.log('[LearningCoach] Early return - missing required data');
      return;
    }

    // Show confirmation dialog immediately
    Alert.alert(
      'Creating Your Unit',
      'Your personalized learning unit is being generated. This will take a few minutes. You can track its progress in your units list.',
      [
        {
          text: 'OK',
          onPress: () => {
            // Navigate back to units list
            navigation.navigate('LessonList');

            // Start unit creation in background with all required coach-driven fields
            // Non-null assertions are safe due to guard above
            createUnit.mutate(
              {
                learnerDesires: sessionState.learnerDesires!,
                unitTitle: sessionState.unitTitle!,
                learningObjectives: sessionState.learningObjectives!,
                targetLessonCount: sessionState.suggestedLessonCount!,
                conversationId: conversationId,
                ownerUserId: user?.id ?? undefined,
              },
              {
                onError: error => {
                  console.error(
                    'Failed to create unit from learning coach',
                    error
                  );
                },
              }
            );
          },
        },
      ],
      { cancelable: false }
    );
  };

  const handleAccept = (): void => {
    if (!conversationId || !sessionState?.proposedBrief) {
      return;
    }

    const brief = sessionState.proposedBrief;

    acceptBrief.mutate(
      {
        conversationId,
        brief,
        userId: user ? String(user.id) : null,
      },
      {
        onSuccess: () => {
          // Brief accepted; user can now proceed to create unit via handleCreateUnit
          // when coach has finalized all required fields
        },
        onError: error => {
          console.error('Failed to accept learning coach brief', error);
        },
      }
    );
  };

  const isAccepting = acceptBrief.isPending || createUnit.isPending;

  const handleCancel = () => {
    Alert.alert(
      'Leave Conversation?',
      'Are you sure you want to go back? Your conversation will be saved.',
      [
        {
          text: 'Stay',
          style: 'cancel',
        },
        {
          text: 'Leave',
          onPress: () => navigation.goBack(),
        },
      ]
    );
  };

  if (!sessionState) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator color={theme.colors.primary} size="large" />
        <Text style={styles.loadingText}>Connecting you with the coach…</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ConversationHeader title="Learning Coach" onClose={handleCancel} />
      <View style={styles.body}>
        {!hasLearnerMessage ? (
          <View style={styles.uploadPrompt}>
            <Text style={styles.uploadPromptTitle}>Share source material</Text>
            <Text style={styles.uploadPromptSubtitle}>
              Upload files or links before your first message so the coach can
              tailor the conversation.
            </Text>
            <Pressable
              style={({ pressed }) => [
                styles.uploadPromptButton,
                {
                  opacity:
                    pressed || !canAttachResource || isCoachLoading ? 0.7 : 1,
                },
              ]}
              onPress={handleAddResource}
              disabled={!canAttachResource || isCoachLoading}
            >
              <Text style={styles.uploadPromptButtonText}>
                Upload source material
              </Text>
            </Pressable>
          </View>
        ) : null}
        <View style={styles.conversationWrapper}>
          <ConversationContainer
            messages={displayMessages}
            suggestedReplies={quickReplies}
            onSendMessage={handleSend}
            onSelectReply={handleQuickReply}
            isLoading={isCoachLoading}
            disabled={isCoachLoading || isAccepting}
            onAttachResource={handleAddResource}
            attachDisabled={
              !canAttachResource ||
              isCoachLoading ||
              isAccepting ||
              isProcessingResource
            }
            composerPlaceholder="Tell the coach what you need"
            loadingMessage="Coach is thinking..."
          />
        </View>
      </View>
      {isProcessingResource ? (
        <View style={styles.processingBanner}>
          <ActivityIndicator color={theme.colors.primary} size="small" />
          <Text style={styles.processingText}>Processing your resource…</Text>
        </View>
      ) : null}
      {sessionState.finalizedTopic && sessionState.learningObjectives ? (
        <View style={styles.finalizedContainer}>
          {sessionState.unitTitle && (
            <Text style={styles.unitTitle}>{sessionState.unitTitle}</Text>
          )}
          {coverageStatus ? (
            <View
              style={[
                styles.coverageBadge,
                coverageStatus.variant === 'success'
                  ? styles.coverageBadgeSuccess
                  : coverageStatus.variant === 'warning'
                    ? styles.coverageBadgeWarning
                    : styles.coverageBadgeNeutral,
              ]}
            >
              <Text style={styles.coverageBadgeText}>
                {coverageStatus.label}
              </Text>
            </View>
          ) : null}
          <Text style={styles.sectionTitle}>Learning Objectives:</Text>
          <View style={styles.objectivesList}>
            {sessionState.learningObjectives.map((objective, idx) => (
              <View key={idx} style={styles.objectiveItem}>
                <Text style={styles.objectiveBullet}>•</Text>
                <Text style={styles.objectiveText}>{objective.title}</Text>
              </View>
            ))}
          </View>
          {sessionState.suggestedLessonCount && (
            <Text style={styles.lessonCountInfo}>
              {sessionState.suggestedLessonCount}{' '}
              {sessionState.suggestedLessonCount === 1 ? 'lesson' : 'lessons'}{' '}
              recommended
            </Text>
          )}
          <Pressable
            style={({ pressed }) => [
              styles.generateButton,
              { opacity: pressed || isAccepting ? 0.7 : 1 },
            ]}
            onPress={handleCreateUnit}
            disabled={isAccepting}
          >
            {isAccepting ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.generateButtonText}>🚀 Generate Unit</Text>
            )}
          </Pressable>
          <Text style={styles.finalizedHint}>
            You can still ask questions or request changes below
          </Text>
        </View>
      ) : sessionState.proposedBrief ? (
        <BriefCard
          brief={sessionState.proposedBrief}
          onAccept={handleAccept}
          onIterate={() =>
            handleQuickReply('Can we try a different direction?')
          }
          isAccepting={isAccepting}
        />
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  body: {
    flex: 1,
  },
  conversationWrapper: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
    gap: 16,
  },
  loadingText: {
    color: theme.colors.text,
    fontSize: 16,
  },
  uploadPrompt: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    gap: 12,
  },
  uploadPromptTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.text,
  },
  uploadPromptSubtitle: {
    fontSize: 14,
    color: theme.colors.textSecondary ?? '#6b7280',
    lineHeight: 20,
  },
  uploadPromptButton: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.primary,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  uploadPromptButtonText: {
    color: theme.colors.surface,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  resourcesContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
    gap: 8,
  },
  resourcesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
  },
  resourcesPills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  resourcePill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.surface,
  },
  resourcePillText: {
    maxWidth: 220,
    color: theme.colors.primary,
    fontSize: 13,
    fontWeight: '600',
  },
  processingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: theme.colors.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
  },
  processingText: {
    color: theme.colors.textSecondary ?? '#6b7280',
    fontSize: 14,
    fontStyle: 'italic',
  },
  finalizedContainer: {
    padding: 16,
    paddingBottom: 20,
    backgroundColor: theme.colors.surface,
    borderTopWidth: 2,
    borderColor: theme.colors.primary,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  unitTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 4,
  },
  objectivesList: {
    gap: 8,
  },
  objectiveItem: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'flex-start',
  },
  objectiveBullet: {
    fontSize: 16,
    color: theme.colors.primary,
    fontWeight: '700',
    marginTop: 2,
  },
  objectiveText: {
    flex: 1,
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 20,
  },
  lessonCountInfo: {
    fontSize: 13,
    color: theme.colors.textSecondary ?? '#999',
    fontWeight: '500',
    marginTop: 4,
  },
  generateButton: {
    backgroundColor: theme.colors.primary,
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
    shadowColor: theme.colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    marginTop: 4,
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  finalizedHint: {
    fontSize: 12,
    color: theme.colors.textSecondary ?? '#999',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  coverageBadge: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  coverageBadgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.text,
  },
  coverageBadgeSuccess: {
    backgroundColor: '#dcfce7',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: '#15803d',
  },
  coverageBadgeWarning: {
    backgroundColor: '#fef3c7',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: '#b45309',
  },
  coverageBadgeNeutral: {
    backgroundColor: theme.colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
  },
});
