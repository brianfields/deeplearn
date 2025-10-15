import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { LearningCoachMessage } from '../models';
import { uiSystemProvider } from '../../ui_system/public';

interface Props {
  readonly message: LearningCoachMessage;
}

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();
const userTextColor = uiSystem.isLightColor(theme.colors.primary)
  ? theme.colors.text
  : theme.colors.surface;

export function MessageBubble({ message }: Props): React.ReactElement {
  const isUser = message.role === 'user';
  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
      <Text style={[styles.text, isUser ? styles.userText : styles.assistantText]}>{message.content}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 16,
    marginBottom: 12,
    maxWidth: '85%',
  },
  userContainer: {
    alignSelf: 'flex-end',
    backgroundColor: theme.colors.primary,
  },
  assistantContainer: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
  },
  text: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: userTextColor,
  },
  assistantText: {
    color: theme.colors.text,
  },
});
