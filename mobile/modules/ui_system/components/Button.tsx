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
import { uiSystemProvider } from '../public';
import type { ButtonProps, Theme } from '../models';

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
  const uiSystem = uiSystemProvider();
  const theme: Theme = uiSystem.getCurrentTheme();

  // Normalize style: allow array/object
  const normalizedStyle = Array.isArray(style)
    ? style.filter(Boolean)
    : style
      ? [style]
      : [];

  const buttonStyle = [
    styles.base,
    getVariantStyle(variant, theme),
    getSizeStyle(size, theme),
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
              ? theme.colors?.primary || '#007AFF'
              : theme.colors?.surface || '#FFFFFF'
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
          <Text style={textStyles}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const getVariantStyle = (variant: string, theme: Theme): ViewStyle => {
  switch (variant) {
    case 'primary':
      return {
        backgroundColor: theme.colors?.primary || '#007AFF',
        borderWidth: 0,
      };
    case 'secondary':
      return {
        backgroundColor: theme.colors?.secondary || '#6C757D',
        borderWidth: 0,
      };
    case 'outline':
      return {
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderColor: theme.colors?.primary || '#007AFF',
      };
    case 'ghost':
      return {
        backgroundColor: 'transparent',
        borderWidth: 0,
      };
    default:
      return {};
  }
};

const getSizeStyle = (size: string, theme: Theme): ViewStyle => {
  switch (size) {
    case 'small':
      return {
        paddingVertical: theme.spacing?.xs || 6,
        paddingHorizontal: theme.spacing?.sm || 10,
        minHeight: 32,
      };
    case 'medium':
      return {
        paddingVertical: theme.spacing?.sm || 10,
        paddingHorizontal: theme.spacing?.md || 14,
        minHeight: 44,
      };
    case 'large':
      return {
        paddingVertical: theme.spacing?.md || 14,
        paddingHorizontal: theme.spacing?.lg || 18,
        minHeight: 56,
      };
    default:
      return {};
  }
};

const getVariantTextStyle = (variant: string, theme: Theme): TextStyle => {
  switch (variant) {
    case 'primary':
    case 'secondary':
      return { color: theme.colors?.surface || '#FFFFFF' };
    case 'outline':
    case 'ghost':
      return { color: theme.colors?.primary || '#007AFF' };
    default:
      return {};
  }
};

const getSizeTextStyle = (size: string, _theme: any): TextStyle => {
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
    borderRadius: 8,
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
