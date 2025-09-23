/**
 * Button Component for React Native Learning App
 *
 * A flexible button component with multiple variants and states
 */

import React, { useCallback, useState } from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  View,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { uiSystemProvider } from '../public';
import type { ButtonProps, Theme } from '../models';
import { useHaptics } from '../hooks/useHaptics';

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  style,
  textStyle,
  testID,
  fullWidth,
}) => {
  const uiSystem = uiSystemProvider();
  const theme: Theme = uiSystem.getCurrentTheme();
  const { trigger } = useHaptics();
  const designSystem = uiSystem.getDesignSystem();
  const [isPressed, setIsPressed] = useState(false);

  // Normalize style: allow array/object
  const normalizedStyle = Array.isArray(style)
    ? style.filter(Boolean)
    : style
      ? [style]
      : [];

  const buttonStyle = [
    styles.base,
    getVariantStyle(variant, theme),
    getSizeStyle(size, theme, fullWidth === true),
    variant === 'primary' && (designSystem?.shadows?.medium as any),
    variant === 'primary' &&
      (isPressed ? { transform: [{ translateY: 1 }] } : null),
    disabled && styles.disabled,
    ...normalizedStyle,
  ];

  const textStyles = [
    styles.text,
    getVariantTextStyle(variant, theme),
    getSizeTextStyle(size, theme),
    disabled && styles.disabledText,
    textStyle,
  ];

  const handlePress = useCallback(() => {
    if (disabled || loading) return;
    // Haptics: medium for primary, light for others per spec guidance
    trigger(variant === 'primary' ? 'medium' : 'light');
    onPress();
  }, [disabled, loading, onPress, trigger, variant]);

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={handlePress}
      onPressIn={() => setIsPressed(true)}
      onPressOut={() => setIsPressed(false)}
      disabled={disabled || loading}
      activeOpacity={0.8}
      testID={testID}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
      hitSlop={
        // Ensure 44x44pt minimum touch target
        size === 'small'
          ? { top: 6, bottom: 6, left: 6, right: 6 }
          : { top: 0, bottom: 0, left: 0, right: 0 }
      }
    >
      {loading ? (
        <ActivityIndicator
          color={
            variant === 'tertiary' || variant === 'secondary'
              ? theme.colors.primary
              : theme.colors.surface
          }
          size="small"
        />
      ) : (
        <View style={styles.content}>
          {icon && (
            <View
              style={[styles.icon, { marginRight: theme.spacing?.xs || 6 }]}
            >
              {icon}
            </View>
          )}
          <Text
            style={[
              textStyles,
              variant === 'tertiary' && isPressed
                ? { textDecorationLine: 'underline' }
                : null,
            ]}
          >
            {title}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const getVariantStyle = (
  variant: NonNullable<ButtonProps['variant']>,
  theme: Theme
): ViewStyle => {
  switch (variant) {
    case 'primary':
      return {
        backgroundColor: theme.colors.primary,
        borderWidth: 0,
      };
    case 'secondary':
      // Outline style
      return {
        backgroundColor: 'transparent',
        borderWidth: StyleSheet.hairlineWidth,
        borderColor: theme.colors?.border,
      };
    case 'tertiary':
      // Text button
      return {
        backgroundColor: 'transparent',
        borderWidth: 0,
      };
    case 'destructive':
      return {
        backgroundColor: theme.colors.error,
        borderWidth: 0,
      };
    // Back-compat aliases handled earlier
    default:
      return {};
  }
};

const getSizeStyle = (
  size: NonNullable<ButtonProps['size']>,
  theme: Theme,
  fullWidth: boolean
): ViewStyle => {
  switch (size) {
    case 'small':
      return {
        paddingVertical: theme.spacing?.xs ?? 4,
        paddingHorizontal: 16,
        minHeight: 32,
        alignSelf: fullWidth ? 'stretch' : 'auto',
      };
    case 'medium':
      return {
        paddingVertical: theme.spacing?.sm ?? 8,
        paddingHorizontal: 20,
        minHeight: 44,
        alignSelf: fullWidth ? 'stretch' : 'auto',
      };
    case 'large':
      return {
        paddingVertical: theme.spacing?.md ?? 16,
        paddingHorizontal: 24,
        minHeight: 52,
        alignSelf: fullWidth ? 'stretch' : 'auto',
      };
    default:
      return {};
  }
};

const getVariantTextStyle = (
  variant: NonNullable<ButtonProps['variant']>,
  theme: Theme
): TextStyle => {
  switch (variant) {
    case 'primary':
    case 'destructive':
      return { color: theme.colors.surface };
    case 'secondary':
    case 'tertiary':
      return {
        color: theme.colors.primary,
        textDecorationLine: variant === 'tertiary' ? 'none' : 'none',
      };
    default:
      return {};
  }
};

const getSizeTextStyle = (
  size: NonNullable<ButtonProps['size']>,
  _theme: any
): TextStyle => {
  switch (size) {
    case 'small':
      return { fontSize: 14, lineHeight: 18 };
    case 'medium':
      return { fontSize: 16, lineHeight: 20 };
    case 'large':
      return { fontSize: 18, lineHeight: 22 };
    default:
      return {};
  }
};

const styles = StyleSheet.create({
  base: {
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  text: {
    textAlign: 'center',
    fontWeight: '600',
  },
  disabled: {
    opacity: 0.5,
  },
  disabledText: {
    opacity: 0.7,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    // marginRight is set dynamically based on theme
  },
});

export default Button;
