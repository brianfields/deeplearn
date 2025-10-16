import React from 'react';
import { View, Pressable, Text, StyleSheet } from 'react-native';
import { uiSystemProvider } from '../../ui_system/public';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

interface Props {
  readonly onSelect: (value: string) => void;
  readonly disabled?: boolean;
}

const QUICK_REPLIES = [
  'I have some prior knowledge',
  'I am a complete beginner',
  'I prefer hands-on projects',
  'Focus on theory',
  'Can we reduce the time commitment?',
];

export function QuickReplies({
  onSelect,
  disabled,
}: Props): React.ReactElement {
  if (disabled) {
    return <View style={styles.container} />;
  }

  return (
    <View style={styles.container}>
      {QUICK_REPLIES.map(reply => (
        <Pressable
          key={reply}
          style={({ pressed }) => [styles.chip, { opacity: pressed ? 0.7 : 1 }]}
          onPress={() => onSelect(reply)}
        >
          <Text style={styles.chipText}>{reply}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
  },
  chip: {
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
    marginRight: 8,
    marginBottom: 8,
  },
  chipText: {
    color: theme.colors.text,
    fontSize: 14,
  },
});
