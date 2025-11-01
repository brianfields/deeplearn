import React from 'react';
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
}

export function ConversationList({
  messages,
  isLoading,
}: Props): React.ReactElement {
  return (
    <FlatList
      data={messages}
      renderItem={({ item }) => <MessageBubble message={item} />}
      keyExtractor={item => item.id}
      contentContainerStyle={styles.container}
      ListFooterComponent={
        <View style={styles.footer}>
          {isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={theme.colors.primary} />
              <Text style={styles.loadingText}>Coach is thinking...</Text>
            </View>
          ) : null}
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
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
