import React from 'react';
import {
  Modal,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type {
  TeachingAssistantContext,
  TeachingAssistantMessage,
} from '../models';
import { uiSystemProvider } from '../../ui_system/public';
import { TeachingAssistantConversation } from './TeachingAssistantConversation';

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

  return (
    <Modal
      animationType="slide"
      visible={visible}
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container} testID="teaching-assistant-modal">
        <View style={styles.header}>
          <Text style={styles.title}>Teaching Assistant</Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close Assistant"
            onPress={onClose}
            style={({ pressed }) => [
              styles.closeButton,
              pressed && styles.closePressed,
            ]}
          >
            <Text style={styles.closeText}>Close</Text>
          </Pressable>
        </View>

        {context ? (
          <View style={styles.contextContainer}>
            {context.lesson?.title ? (
              <Text style={styles.contextLine}>
                Lesson:{' '}
                <Text style={styles.contextValue}>{context.lesson.title}</Text>
              </Text>
            ) : null}
            {progressPercentage !== null ? (
              <Text style={styles.contextLine}>
                Progress:{' '}
                <Text style={styles.contextValue}>{progressPercentage}%</Text>
              </Text>
            ) : null}
          </View>
        ) : null}

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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: theme.colors.text,
  },
  closeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: theme.colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
  },
  closePressed: {
    opacity: 0.7,
  },
  closeText: {
    color: theme.colors.text,
    fontWeight: '500',
  },
  contextContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  contextLine: {
    color: theme.colors.textSecondary ?? '#666',
    marginBottom: 4,
  },
  contextValue: {
    color: theme.colors.text,
    fontWeight: '600',
  },
  conversationContainer: {
    flex: 1,
  },
});
