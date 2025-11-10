import React, { useRef, useEffect } from 'react';
import {
  FlatList,
  View,
  StyleSheet,
  ActivityIndicator,
  Text,
} from 'react-native';
import type { LearningCoachMessage, TeachingAssistantMessage } from '../models';
import { MessageBubble } from './MessageBubble';
import { uiSystemProvider } from '../../ui_system/public';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

type ConversationMessage = LearningCoachMessage | TeachingAssistantMessage;

interface Props {
  readonly messages: ConversationMessage[];
  readonly isLoading?: boolean;
  readonly loadingMessage?: string;
}

export function ConversationList({
  messages,
  isLoading,
  loadingMessage,
}: Props): React.ReactElement {
  const flatListRef = useRef<FlatList<ConversationMessage>>(null);

  // Auto-scroll to the end when messages change or loading state changes
  useEffect(() => {
    if (flatListRef.current && (messages.length > 0 || isLoading)) {
      // Use a small delay to ensure the FlatList has finished rendering
      const timer = setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messages, isLoading]);

  // Also scroll on content size change (for streaming responses)
  const handleContentSizeChange = (): void => {
    flatListRef.current?.scrollToEnd({ animated: true });
  };

  return (
    <FlatList
      ref={flatListRef}
      data={messages}
      renderItem={({ item }) => <MessageBubble message={item} />}
      keyExtractor={item => item.id}
      contentContainerStyle={styles.container}
      maintainVisibleContentPosition={{ minIndexForVisible: 0 }}
      onContentSizeChange={handleContentSizeChange}
      ListFooterComponent={
        <View style={styles.footer}>
          {isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={theme.colors.primary} />
              <Text style={styles.loadingText}>
                {loadingMessage ?? 'Coach is thinking...'}
              </Text>
            </View>
          ) : null}
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 16,
    // Add substantial bottom padding to ensure messages aren't covered by
    // QuickReplies and Composer when scrolling to end. This accounts for:
    // - QuickReplies (~60px)
    // - Composer (~60px)
    // - Safe area and margin (~40px)
    paddingBottom: 200,
  },
  footer: {
    minHeight: 32,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  loadingText: {
    color: theme.colors.textSecondary ?? '#999',
    fontSize: 14,
    fontStyle: 'italic',
  },
});
