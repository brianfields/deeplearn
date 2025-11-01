import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import { uiSystemProvider } from '../../ui_system/public';
import { infrastructureProvider } from '../../infrastructure/public';

interface Props {
  readonly onPress: () => void;
  readonly style?: ViewStyle;
  readonly disabled?: boolean;
}

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

const infrastructure = infrastructureProvider();

export function TeachingAssistantButton({
  onPress,
  style,
  disabled,
}: Props): React.ReactElement {
  const [isOnline, setIsOnline] = useState<boolean>(infrastructure.isOnline());

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOnline(state.isConnected ?? false);
    });
    return () => {
      unsubscribe();
    };
  }, []);

  const statusStyles = useMemo(() => {
    const onlineColor = theme.colors.success ?? '#2ecc71';
    const offlineColor = theme.colors.error ?? '#e74c3c';
    return {
      indicator: {
        backgroundColor: isOnline ? onlineColor : offlineColor,
      },
      button: {
        opacity: isOnline && !disabled ? 1 : 0.7,
      },
    };
  }, [disabled, isOnline]);

  const labelColor = useMemo(() => {
    return uiSystem.isLightColor(theme.colors.primary)
      ? theme.colors.text
      : theme.colors.surface;
  }, []);

  const handlePress = () => {
    if (disabled) {
      return;
    }

    if (!isOnline) {
      Alert.alert(
        'Offline',
        'Teaching assistant requires internet connection to respond.'
      );
      return;
    }
    onPress();
  };

  return (
    <Pressable
      testID="teaching-assistant-button"
      onPress={handlePress}
      style={({ pressed }) => [
        styles.button,
        style,
        statusStyles.button,
        pressed ? styles.buttonPressed : null,
      ]}
      accessibilityRole="button"
      accessibilityState={{ disabled: !isOnline || !!disabled }}
      accessibilityLabel="Ask"
    >
      <View style={[styles.statusDot, statusStyles.indicator]} />
      <Text style={[styles.label, { color: labelColor }]}>Ask</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 18,
    paddingVertical: 14,
    borderRadius: 999,
    backgroundColor: theme.colors.primary,
    opacity: 0.85,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 4,
  },
  buttonPressed: {
    transform: [{ scale: 0.97 }],
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
  },
});
