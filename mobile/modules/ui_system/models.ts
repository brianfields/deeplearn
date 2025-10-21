/**
 * UI System Models
 *
 * Types for theme, components, and design system.
 */

import React from 'react';
import type { StyleProp, ViewStyle } from 'react-native';

// ================================
// Theme Types
// ================================

export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

export interface Spacing {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

export interface Typography {
  heading1: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  heading2: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  heading3: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  body: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  caption: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
}

export interface Theme {
  colors: ThemeColors;
  spacing: Spacing;
  typography: Typography;
}

// ================================
// Component Types
// ================================

export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'tertiary' | 'destructive';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
  style?: any;
  textStyle?: any;
  testID?: string;
}

export interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: keyof Spacing | number;
  margin?: keyof Spacing | number;
  style?: any;
  onPress?: () => void;
  disabled?: boolean;
}

export interface ProgressProps {
  progress: number; // 0-100
  variant?: 'linear' | 'circular';
  size?: 'small' | 'medium' | 'large';
  color?: string;
  backgroundColor?: string;
  showLabel?: boolean;
  label?: string;
  animated?: boolean;
  style?: any;
}

export interface ArtworkImageProps {
  title: string;
  imageUrl?: string | null;
  description?: string | null;
  variant?: 'thumbnail' | 'hero';
  style?: any;
  testID?: string;
}

export interface SliderProps {
  value: number;
  minimumValue?: number;
  maximumValue: number;
  step?: number;
  onValueChange?: (value: number) => void;
  onSlidingStart?: (value: number) => void;
  onSlidingComplete?: (value: number) => void;
  disabled?: boolean;
  minimumTrackTintColor?: string;
  maximumTrackTintColor?: string;
  thumbTintColor?: string;
  showValueLabels?: boolean;
  formatValueLabel?: (value: number) => string;
  minimumLabel?: string;
  maximumLabel?: string;
  containerStyle?: StyleProp<ViewStyle>;
  sliderStyle?: StyleProp<ViewStyle>;
  testID?: string;
}

// ================================
// Responsive Types
// ================================

export interface ResponsiveConfig {
  screenWidth: number;
  screenHeight: number;
  isSmallScreen: boolean;
  isMediumScreen: boolean;
  isLargeScreen: boolean;
  headerHeight: number;
  statusBarHeight: number;
  tabBarHeight: number;
}

export interface ShadowConfig {
  small: any;
  medium: any;
  large: any;
}

export interface AnimationConfig {
  fast: number;
  normal: number;
  slow: number;
  easeInOut: string;
  easeIn: string;
  easeOut: string;
}

// ================================
// Utility Types
// ================================

export interface UtilityFunctions {
  margin: (size: keyof Spacing | number) => any;
  marginTop: (size: keyof Spacing | number) => any;
  marginBottom: (size: keyof Spacing | number) => any;
  marginHorizontal: (size: keyof Spacing | number) => any;
  marginVertical: (size: keyof Spacing | number) => any;
  padding: (size: keyof Spacing | number) => any;
  paddingTop: (size: keyof Spacing | number) => any;
  paddingBottom: (size: keyof Spacing | number) => any;
  paddingHorizontal: (size: keyof Spacing | number) => any;
  paddingVertical: (size: keyof Spacing | number) => any;
  isLightColor: (color: string) => boolean;
  responsiveSize: (base: number, factor?: number) => number;
  clamp: (value: number, min: number, max: number) => number;
}

// ================================
// Design System DTOs
// ================================

export interface DesignSystemConfig {
  theme: Theme;
  responsive: ResponsiveConfig;
  shadows: ShadowConfig;
  animations: AnimationConfig;
  utils: UtilityFunctions;
}

export interface ThemeManagerState {
  currentTheme: Theme;
  isDarkMode: boolean;
  systemTheme: 'light' | 'dark' | 'auto';
}
