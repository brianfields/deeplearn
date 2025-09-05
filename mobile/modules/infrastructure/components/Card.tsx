/**
 * Card Component for React Native Learning App
 *
 * A flexible card container with consistent styling
 */

import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { useTheme } from '../module_api/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  elevated?: boolean;
  padding?: keyof typeof defaultSpacing | number;
}

const defaultSpacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const Card: React.FC<CardProps> = ({
  children,
  style,
  elevated = true,
  padding = 'md',
}) => {
  const { theme } = useTheme();

  const paddingValue =
    typeof padding === 'number'
      ? padding
      : theme.spacing[padding] || defaultSpacing[padding];

  const cardStyle = [
    styles.base,
    {
      backgroundColor: theme.colors.surface,
      borderColor: theme.colors.border,
      padding: paddingValue,
    },
    elevated && theme.shadows?.medium,
    style,
  ];

  return <View style={cardStyle}>{children}</View>;
};

const styles = StyleSheet.create({
  base: {
    borderRadius: 12,
    borderWidth: 1,
  },
});

export default Card;
