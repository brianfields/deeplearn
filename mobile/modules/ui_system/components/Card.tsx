/**
 * Card Component for React Native Learning App
 *
 * A flexible card container with consistent styling
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { internalUiSystemProvider } from '../internalProvider';
import type { CardProps } from '../models';

const uiSystemProvider = internalUiSystemProvider;

export const Card: React.FC<CardProps> = ({
  children,
  style,
  variant = 'default',
  padding = 'md',
  margin,
  onPress,
  disabled = false,
  testID,
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

  // Flatten style to safely extract pointerEvents and avoid nested arrays
  const flattened = StyleSheet.flatten(style) || ({} as any);
  const { pointerEvents, ...otherStyles } = flattened as any;

  const cardStyle = [
    styles.base,
    {
      backgroundColor: theme.colors.surface,
      borderColor: theme.colors.border,
      padding: paddingValue,
      margin: marginValue,
    },
    // Default card: hairline border + Raised elevation per Weimar Edge
    variant === 'default' && { borderWidth: StyleSheet.hairlineWidth },
    variant === 'default' && designSystem.shadows?.medium,
    // Elevated variant: stronger elevation
    variant === 'elevated' && designSystem.shadows?.large,
    // Outlined variant: hairline border, no shadow
    variant === 'outlined' && { borderWidth: StyleSheet.hairlineWidth },
    disabled && styles.disabled,
    otherStyles,
    pointerEvents && { pointerEvents },
  ];

  const Component = onPress ? TouchableOpacity : View;

  return (
    <Component
      style={cardStyle}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={onPress ? 0.8 : 1}
      testID={testID}
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
