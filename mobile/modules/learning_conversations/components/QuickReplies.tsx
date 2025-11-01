import React from 'react';
import { View, Pressable, Text, StyleSheet } from 'react-native';
import { uiSystemProvider } from '../../ui_system/public';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

interface Props {
  readonly onSelect: (value: string) => void;
  readonly disabled?: boolean;
  readonly replies: string[];
}

export function QuickReplies({
  onSelect,
  disabled,
  replies,
}: Props): React.ReactElement {
  // Don't render if disabled or no replies available
  if (disabled || replies.length === 0) {
    return <View style={styles.container} />;
  }

  return (
    <View style={styles.container}>
      {replies.map(reply => (
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
