import React from 'react';
import type { TeachingAssistantMessage } from '../models';
import { ConversationContainer } from './ConversationContainer';

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
    <ConversationContainer
      messages={messages}
      suggestedReplies={replies}
      onSendMessage={onSend}
      onSelectReply={onSelectReply}
      isLoading={isLoading}
      disabled={disabled}
      onAttachResource={onAttachResource}
      attachDisabled={attachDisabled}
      composerPlaceholder="Ask the teaching assistant..."
      loadingMessage="Teaching assistant is responding..."
    />
  );
}
