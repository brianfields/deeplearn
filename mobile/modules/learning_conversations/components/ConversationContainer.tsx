import React from 'react';
import { View, StyleSheet } from 'react-native';
import type { LearningCoachMessage, TeachingAssistantMessage } from '../models';
import { ConversationList } from './ConversationList';
import { QuickReplies } from './QuickReplies';
import { Composer } from './Composer';

type ConversationMessage = LearningCoachMessage | TeachingAssistantMessage;

interface Props {
  readonly messages: ConversationMessage[];
  readonly suggestedReplies: readonly string[];
  readonly onSendMessage: (message: string) => void;
  readonly onSelectReply: (message: string) => void;
  readonly isLoading?: boolean;
  readonly disabled?: boolean;
  readonly onAttachResource?: () => void;
  readonly attachDisabled?: boolean;
  readonly composerPlaceholder?: string;
  readonly loadingMessage?: string;
}

/**
 * ConversationContainer is a reusable wrapper component that provides a consistent UI
 * for conversation-based interactions (e.g., Learning Coach, Teaching Assistant).
 *
 * It composes three main sub-components:
 * - ConversationList: Displays all messages (user and assistant)
 * - QuickReplies: Shows suggested quick reply options
 * - Composer: Text input for sending messages
 *
 * This ensures both the Learning Coach and Teaching Assistant have identical visual appearance,
 * reducing maintenance burden and improving consistency.
 */
export function ConversationContainer({
  messages,
  suggestedReplies,
  onSendMessage,
  onSelectReply,
  isLoading = false,
  disabled = false,
  onAttachResource,
  attachDisabled = false,
  composerPlaceholder,
  loadingMessage,
}: Props): React.ReactElement {
  return (
    <View style={styles.container}>
      <ConversationList
        messages={messages}
        isLoading={isLoading}
        loadingMessage={loadingMessage}
      />
      <QuickReplies
        onSelect={onSelectReply}
        disabled={disabled || suggestedReplies.length === 0}
        replies={suggestedReplies as string[]}
      />
      <Composer
        onSend={onSendMessage}
        disabled={disabled}
        onAttach={onAttachResource}
        attachDisabled={attachDisabled}
        placeholderText={composerPlaceholder}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
