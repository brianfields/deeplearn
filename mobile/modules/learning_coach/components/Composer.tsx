import React, { useState } from 'react';
import { View, TextInput, Pressable, Text, StyleSheet } from 'react-native';
import { uiSystemProvider } from '../../ui_system/public';

interface Props {
  readonly onSend: (message: string) => void;
  readonly disabled?: boolean;
}

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();
const sendTextColor = uiSystem.isLightColor(theme.colors.primary)
  ? theme.colors.text
  : theme.colors.surface;

export function Composer({ onSend, disabled }: Props): React.ReactElement {
  const [value, setValue] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isSending) {
      return;
    }
    setIsSending(true);
    onSend(trimmed);
    setValue('');
  };

  // Reset sending state when input changes or when disabled changes
  React.useEffect(() => {
    if (value || !disabled) {
      setIsSending(false);
    }
  }, [value, disabled]);

  return (
    <View style={styles.container}>
      <TextInput
        value={value}
        onChangeText={setValue}
        placeholder="Tell the coach what you need"
        placeholderTextColor={theme.colors.textSecondary ?? '#999'}
        style={styles.input}
        editable={!disabled}
        multiline
      />
      <Pressable
        style={({ pressed }) => [
          styles.button,
          { opacity: pressed || disabled || isSending ? 0.6 : 1 },
        ]}
        onPress={handleSend}
        disabled={disabled || isSending}
      >
        <Text style={styles.buttonText}>Send</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: theme.colors.surface,
    color: theme.colors.text,
  },
  button: {
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: theme.colors.primary,
    marginLeft: 12,
  },
  buttonText: {
    color: sendTextColor,
    fontWeight: '600',
  },
});
