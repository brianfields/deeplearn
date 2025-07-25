/**
 * Button Component for React Native Learning App
 *
 * A flexible button component with multiple variants and states
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  View,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { colors, spacing, shadows } from '@/utils/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

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
}) => {
  const buttonStyle = [
    styles.base,
    styles[variant],
    styles[size],
    disabled && styles.disabled,
    style,
  ];

  const textStyles = [
    styles.text,
    styles[`${variant}Text` as keyof typeof styles],
    styles[`${size}Text` as keyof typeof styles],
    disabled && styles.disabledText,
    textStyle,
  ];

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator
          color={
            variant === 'outline' || variant === 'ghost'
              ? colors.primary
              : colors.surface
          }
          size="small"
        />
      ) : (
        <View style={styles.content}>
          {icon && <View style={styles.icon}>{icon}</View>}
          <Text style={textStyles}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    ...shadows.small,
  },

  // Variants
  primary: {
    backgroundColor: colors.primary,
    borderWidth: 0,
  },

  secondary: {
    backgroundColor: colors.secondary,
    borderWidth: 0,
  },

  outline: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.primary,
  },

  ghost: {
    backgroundColor: 'transparent',
    borderWidth: 0,
  },

  // Sizes
  small: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    minHeight: 32,
  },

  medium: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    minHeight: 44,
  },

  large: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    minHeight: 56,
  },

  // Text base
  text: {
    textAlign: 'center',
    fontWeight: '600',
  },

  // Text variants
  primaryText: {
    color: colors.surface,
  },

  secondaryText: {
    color: colors.surface,
  },

  outlineText: {
    color: colors.primary,
  },

  ghostText: {
    color: colors.primary,
  },

  // Text sizes
  smallText: {
    fontSize: 14,
    lineHeight: 18,
  },

  mediumText: {
    fontSize: 16,
    lineHeight: 20,
  },

  largeText: {
    fontSize: 18,
    lineHeight: 22,
  },

  // States
  disabled: {
    opacity: 0.5,
  },

  disabledText: {
    opacity: 0.7,
  },

  // Layout
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },

  icon: {
    marginRight: spacing.xs,
  },
});

export default Button;
