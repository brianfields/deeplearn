/**
 * Theme System for React Native Learning App
 *
 * Provides consistent colors, typography, spacing, and styling utilities
 * across the mobile application
 */

import { Dimensions, Platform } from 'react-native';
import { tokens } from '../tokens';
import type {
  Theme,
  ThemeColors,
  Spacing,
  Typography,
  ResponsiveConfig,
  ShadowConfig,
  AnimationConfig,
  UtilityFunctions,
} from '../models';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// ================================
// Colors
// ================================

export const colors: ThemeColors = {
  // Map Weimar Edge tokens → app theme roles
  primary: tokens.color.accent600, // Petrol blue as primary brand
  secondary: tokens.color.gilt500, // Tarnished gold as secondary/accent
  accent: tokens.color.accent400, // Lighter petrol for accents

  // Background / surfaces
  background: tokens.color.paper0, // Bone paper
  surface: '#FFFFFF', // Keep white for elevated cards where needed

  // Text
  text: tokens.color.ink900, // Charcoal noir
  // Use ink at 80% opacity per spec for secondary text on light backgrounds
  textSecondary: 'rgba(13, 14, 16, 0.8)',

  // UI / feedback
  border: tokens.color.accent200,
  success: tokens.color.emerald500,
  warning: tokens.color.amber600,
  error: tokens.color.rouge600,
  info: tokens.color.sky500,
};

// ================================
// Spacing
// ================================

export const spacing: Spacing = {
  // Derive named scale from token space array
  xs: tokens.space[1], // 4
  sm: tokens.space[2], // 8
  md: tokens.space[4], // 16
  lg: tokens.space[6], // 24
  xl: tokens.space[8], // 32
  xxl: tokens.space[10], // 48
};

// ================================
// Typography
// ================================

export const typography: Typography = {
  // Map Weimar Edge typographic scale into existing keys
  heading1: {
    fontSize: tokens.type.h1.size,
    fontWeight:
      Platform.OS === 'ios' ? tokens.type.h1.weight : ('bold' as const),
    lineHeight: tokens.type.h1.line,
  },
  heading2: {
    fontSize: tokens.type.h2.size,
    fontWeight:
      Platform.OS === 'ios' ? tokens.type.h2.weight : ('bold' as const),
    lineHeight: tokens.type.h2.line,
  },
  heading3: {
    fontSize: tokens.type.title.size,
    fontWeight:
      Platform.OS === 'ios' ? tokens.type.title.weight : ('bold' as const),
    lineHeight: tokens.type.title.line,
  },
  body: {
    fontSize: tokens.type.body.size,
    fontWeight:
      Platform.OS === 'ios' ? tokens.type.body.weight : ('normal' as const),
    lineHeight: tokens.type.body.line,
  },
  caption: {
    fontSize: tokens.type.caption.size,
    fontWeight:
      Platform.OS === 'ios' ? tokens.type.caption.weight : ('normal' as const),
    lineHeight: tokens.type.caption.line,
  },
};

// ================================
// Typography Utility Function
// ================================

/**
 * Helper function to create properly typed text styles
 * Fixes fontWeight type issues throughout the app
 */
export const textStyle = (style: any) => style as any;

// ================================
// Complete Theme
// ================================

export const theme: Theme = {
  colors,
  spacing,
  typography,
};

// ================================
// Responsive Utilities
// ================================

export const responsive: ResponsiveConfig = {
  // Screen dimensions
  screenWidth,
  screenHeight,

  // Breakpoints
  isSmallScreen: screenWidth < 375,
  isMediumScreen: screenWidth >= 375 && screenWidth < 768,
  isLargeScreen: screenWidth >= 768,

  // Safe areas (simplified - you might want to use react-native-safe-area-context)
  headerHeight: Platform.OS === 'ios' ? 44 : 56,
  statusBarHeight: Platform.OS === 'ios' ? 20 : 24,
  tabBarHeight: Platform.OS === 'ios' ? 83 : 56,
};

// ================================
// Common Shadows
// ================================

export const shadows: ShadowConfig = {
  small: Platform.select({
    ios: {
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.18,
      shadowRadius: 1.0,
    },
    android: {
      elevation: 2,
    },
  }),
  medium: Platform.select({
    ios: {
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.22,
      shadowRadius: 2.22,
    },
    android: {
      elevation: 4,
    },
  }),
  large: Platform.select({
    ios: {
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 4.65,
    },
    android: {
      elevation: 8,
    },
  }),
};

// ================================
// Common Styles
// ================================

export const commonStyles = {
  // Container styles
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  safeArea: {
    flex: 1,
    backgroundColor: colors.surface,
    paddingTop: responsive.statusBarHeight,
  },

  centered: {
    flex: 1,
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
  },

  // Card styles
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    ...shadows.medium,
  },

  // Button styles
  button: {
    borderRadius: 8,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
  },

  buttonPrimary: {
    backgroundColor: colors.primary,
  },

  buttonSecondary: {
    backgroundColor: colors.secondary,
  },

  buttonText: {
    ...typography.body,
    fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
    color: colors.surface,
  },

  // Text styles
  textHeading1: {
    ...typography.heading1,
    color: colors.text,
  },

  textHeading2: {
    ...typography.heading2,
    color: colors.text,
  },

  textHeading3: {
    ...typography.heading3,
    color: colors.text,
  },

  textBody: {
    ...typography.body,
    color: colors.text,
  },

  textCaption: {
    ...typography.caption,
    color: colors.textSecondary,
  },

  // Input styles
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: spacing.sm,
    ...typography.body,
    color: colors.text,
    backgroundColor: colors.surface,
  },

  // Progress styles
  progressContainer: {
    height: 8,
    backgroundColor: colors.border,
    borderRadius: 4,
    overflow: 'hidden' as const,
  },

  progressBar: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 4,
  },

  // Layout helpers
  row: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
  },

  column: {
    flexDirection: 'column' as const,
  },

  spaceBetween: {
    justifyContent: 'space-between' as const,
  },

  spaceAround: {
    justifyContent: 'space-around' as const,
  },

  spaceEvenly: {
    justifyContent: 'space-evenly' as const,
  },
};

// ================================
// Animation Presets
// ================================

export const animations: AnimationConfig = {
  // Durations
  fast: 160,
  normal: 220,
  slow: 320,

  // Easing curves
  // Align with Weimar Edge timing/easing specs
  easeInOut: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  easeIn: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  easeOut: 'cubic-bezier(0.4, 0.0, 1, 1)',
};

// ================================
// Utility Functions
// ================================

export const utils: UtilityFunctions = {
  /**
   * Create margin/padding shortcuts
   */
  margin: (size: keyof Spacing | number) => ({
    margin: typeof size === 'number' ? size : spacing[size],
  }),

  marginTop: (size: keyof Spacing | number) => ({
    marginTop: typeof size === 'number' ? size : spacing[size],
  }),

  marginBottom: (size: keyof Spacing | number) => ({
    marginBottom: typeof size === 'number' ? size : spacing[size],
  }),

  marginHorizontal: (size: keyof Spacing | number) => ({
    marginHorizontal: typeof size === 'number' ? size : spacing[size],
  }),

  marginVertical: (size: keyof Spacing | number) => ({
    marginVertical: typeof size === 'number' ? size : spacing[size],
  }),

  padding: (size: keyof Spacing | number) => ({
    padding: typeof size === 'number' ? size : spacing[size],
  }),

  paddingTop: (size: keyof Spacing | number) => ({
    paddingTop: typeof size === 'number' ? size : spacing[size],
  }),

  paddingBottom: (size: keyof Spacing | number) => ({
    paddingBottom: typeof size === 'number' ? size : spacing[size],
  }),

  paddingHorizontal: (size: keyof Spacing | number) => ({
    paddingHorizontal: typeof size === 'number' ? size : spacing[size],
  }),

  paddingVertical: (size: keyof Spacing | number) => ({
    paddingVertical: typeof size === 'number' ? size : spacing[size],
  }),

  /**
   * Check if color is light or dark
   */
  isLightColor: (color: string): boolean => {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 155;
  },

  /**
   * Create responsive size based on screen width
   */
  responsiveSize: (base: number, factor: number = 0.1): number => {
    return base + (screenWidth - 375) * factor;
  },

  /**
   * Clamp value between min and max
   */
  clamp: (value: number, min: number, max: number): number => {
    return Math.min(Math.max(value, min), max);
  },
};

export default theme;
