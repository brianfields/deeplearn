import React from 'react';
import { Modal, SafeAreaView, StyleSheet, View } from 'react-native';
import type {
  TeachingAssistantContext,
  TeachingAssistantMessage,
} from '../models';
import { uiSystemProvider } from '../../ui_system/public';
import { reducedMotion } from '../../ui_system/utils/motion';
import { TeachingAssistantConversation } from './TeachingAssistantConversation';
import { ConversationHeader } from './ConversationHeader';

interface Props {
  readonly visible: boolean;
  readonly onClose: () => void;
  readonly messages: TeachingAssistantMessage[];
  readonly suggestedQuickReplies: readonly string[];
  readonly onSend: (message: string) => void;
  readonly onSelectReply: (message: string) => void;
  readonly context: TeachingAssistantContext | null;
  readonly isLoading?: boolean;
  readonly disabled?: boolean;
}

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

/**
 * TeachingAssistantModal
 *
 * Displays an overlay modal for the teaching assistant conversation.
 *
 * NOTE: Future refactoring - This component should be migrated to a proper
 * React Navigation modal screen for better consistency, accessibility, and
 * Android back button handling. See the architecture audit for details.
 *
 * Animation & Accessibility:
 * - Respects reduced motion setting (no animation when enabled)
 * - Uses appropriate animation timing
 * - On Android: hardware back button handled via onRequestClose
 */
export function TeachingAssistantModal({
  visible,
  onClose,
  messages,
  suggestedQuickReplies,
  onSend,
  onSelectReply,
  context,
  isLoading,
  disabled,
}: Props): React.ReactElement {
  const rawProgress = context?.session?.progress_percentage;
  const progressPercentage =
    typeof rawProgress === 'number' ? Math.round(rawProgress) : null;

  // Build subtitle from context
  const subtitle = (() => {
    const parts: string[] = [];
    if (context?.lesson?.title) {
      parts.push(`Lesson: ${context.lesson.title}`);
    }
    if (progressPercentage !== null) {
      parts.push(`Progress: ${progressPercentage}%`);
    }
    return parts.length > 0 ? parts.join(' • ') : undefined;
  })();

  // Use no animation if reduced motion is enabled
  const animationType = reducedMotion.enabled ? 'none' : 'slide';

  return (
    <Modal
      animationType={animationType}
      visible={visible}
      presentationStyle="pageSheet"
      onRequestClose={onClose}
      testID="teaching-assistant-modal"
    >
      <SafeAreaView style={styles.container}>
        <ConversationHeader
          title="Teaching Assistant"
          onClose={onClose}
          subtitle={subtitle}
        />

        <View style={styles.conversationContainer}>
          <TeachingAssistantConversation
            messages={messages}
            suggestedQuickReplies={suggestedQuickReplies}
            onSend={onSend}
            onSelectReply={onSelectReply}
            isLoading={isLoading}
            disabled={disabled}
          />
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  conversationContainer: {
    flex: 1,
  },
});
