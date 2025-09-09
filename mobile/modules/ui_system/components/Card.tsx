/**
 * Card Component for React Native Learning App
 *
 * A flexible card container with consistent styling
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { uiSystemProvider } from '../public';
import type { CardProps } from '../models';

export const Card: React.FC<CardProps> = ({
  children,
  style,
  variant = 'default',
  padding = 'md',
  margin,
  onPress,
  disabled = false,
}) => {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const designSystem = uiSystem.getDesignSystem();

  const paddingValue =
    typeof padding === 'number'
      ? padding
      : uiSystem.getSpacing(padding as keyof typeof theme.spacing);

  const marginValue = margin
    ? typeof margin === 'number'
      ? margin
      : uiSystem.getSpacing(margin as keyof typeof theme.spacing)
    : 0;

  const cardStyle = [
    styles.base,
    {
      backgroundColor: theme.colors.surface,
      borderColor: theme.colors.border,
      padding: paddingValue,
      margin: marginValue,
    },
    variant === 'elevated' && designSystem.shadows?.medium,
    variant === 'outlined' && { borderWidth: 1 },
    disabled && styles.disabled,
    style,
  ];

  const Component = onPress ? TouchableOpacity : View;

  return (
    <Component
      style={cardStyle}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={onPress ? 0.8 : 1}
    >
      {children}
    </Component>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: 12,
  },
  disabled: {
    opacity: 0.6,
  },
});

export default Card;
