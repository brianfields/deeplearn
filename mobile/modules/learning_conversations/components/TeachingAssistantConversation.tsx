import React from 'react';
import type { TeachingAssistantMessage } from '../models';
import { ConversationList } from './ConversationList';
import { QuickReplies } from './QuickReplies';
import { Composer } from './Composer';
import { StyleSheet, View } from 'react-native';

interface Props {
  readonly messages: TeachingAssistantMessage[];
  readonly suggestedQuickReplies: readonly string[];
  readonly onSend: (message: string) => void;
  readonly onSelectReply: (message: string) => void;
  readonly isLoading?: boolean;
  readonly disabled?: boolean;
  readonly onAttachResource?: () => void;
  readonly attachDisabled?: boolean;
}

export function TeachingAssistantConversation({
  messages,
  suggestedQuickReplies,
  onSend,
  onSelectReply,
  isLoading,
  disabled,
  onAttachResource,
  attachDisabled,
}: Props): React.ReactElement {
  const replies = Array.from(suggestedQuickReplies);

  return (
    <View style={styles.container}>
      <ConversationList messages={messages} isLoading={isLoading} />
      <QuickReplies
        replies={replies}
        disabled={disabled || replies.length === 0}
        onSelect={onSelectReply}
      />
      <Composer
        onSend={onSend}
        disabled={disabled}
        onAttach={onAttachResource}
        attachDisabled={attachDisabled}
        placeholderText="Ask the teaching assistant..."
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
