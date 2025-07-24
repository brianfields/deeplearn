/**
 * Theme System for React Native Learning App
 *
 * Provides consistent colors, typography, spacing, and styling utilities
 * across the mobile application
 */

import { Dimensions, Platform } from 'react-native'
import type { Theme, ThemeColors, Spacing, Typography } from '@/types'

const { width: screenWidth, height: screenHeight } = Dimensions.get('window')

// ================================
// Colors
// ================================

export const colors: ThemeColors = {
  // Primary colors (Duolingo-inspired)
  primary: '#1CB0F6',      // Bright blue
  secondary: '#00CD9C',    // Teal green
  accent: '#FF9600',       // Orange

  // Background colors
  background: '#F7F8FA',   // Light gray
  surface: '#FFFFFF',      // White

  // Text colors
  text: '#2B2D42',         // Dark blue-gray
  textSecondary: '#5E6B73', // Medium gray

  // UI colors
  border: '#E5E7EB',       // Light border
  success: '#22C55E',      // Green
  warning: '#F59E0B',      // Amber
  error: '#EF4444',        // Red
  info: '#3B82F6'          // Blue
}

// ================================
// Spacing
// ================================

export const spacing: Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48
}

// ================================
// Typography
// ================================

export const typography: Typography = {
  heading1: {
    fontSize: 32,
    fontWeight: Platform.OS === 'ios' ? '700' : 'bold',
    lineHeight: 40
  },
  heading2: {
    fontSize: 24,
    fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
    lineHeight: 32
  },
  heading3: {
    fontSize: 20,
    fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
    lineHeight: 28
  },
  body: {
    fontSize: 16,
    fontWeight: Platform.OS === 'ios' ? '400' : 'normal',
    lineHeight: 24
  },
  caption: {
    fontSize: 14,
    fontWeight: Platform.OS === 'ios' ? '400' : 'normal',
    lineHeight: 20
  }
}

// ================================
// Typography Utility Function
// ================================

/**
 * Helper function to create properly typed text styles
 * Fixes fontWeight type issues throughout the app
 */
export const textStyle = (style: any) => style as any

// ================================
// Complete Theme
// ================================

export const theme: Theme = {
  colors,
  spacing,
  typography
}

// ================================
// Responsive Utilities
// ================================

export const responsive = {
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

  // Responsive sizing functions
  wp: (percentage: number) => (screenWidth * percentage) / 100,
  hp: (percentage: number) => (screenHeight * percentage) / 100,

  // Responsive font sizing
  fontSize: (size: number) => {
    if (screenWidth < 350) return size * 0.9
    if (screenWidth > 400) return size * 1.1
    return size
  }
}

// ================================
// Common Shadows
// ================================

export const shadows = {
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
}

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
}

// ================================
// Animation Presets
// ================================

export const animations = {
  // Durations
  fast: 200,
  normal: 300,
  slow: 500,

  // Easing curves
  easeInOut: 'ease-in-out',
  easeIn: 'ease-in',
  easeOut: 'ease-out',

  // Common animations
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },

  slideInUp: {
    from: {
      opacity: 0,
      transform: [{ translateY: 50 }]
    },
    to: {
      opacity: 1,
      transform: [{ translateY: 0 }]
    },
  },

  slideInDown: {
    from: {
      opacity: 0,
      transform: [{ translateY: -50 }]
    },
    to: {
      opacity: 1,
      transform: [{ translateY: 0 }]
    },
  },

  scaleIn: {
    from: {
      opacity: 0,
      transform: [{ scale: 0.8 }]
    },
    to: {
      opacity: 1,
      transform: [{ scale: 1 }]
    },
  },
}

// ================================
// Utility Functions
// ================================

export const utils = {
  /**
   * Create margin/padding shortcuts
   */
  margin: (size: keyof Spacing | number) => ({
    margin: typeof size === 'number' ? size : spacing[size]
  }),

  marginTop: (size: keyof Spacing | number) => ({
    marginTop: typeof size === 'number' ? size : spacing[size]
  }),

  marginBottom: (size: keyof Spacing | number) => ({
    marginBottom: typeof size === 'number' ? size : spacing[size]
  }),

  marginHorizontal: (size: keyof Spacing | number) => ({
    marginHorizontal: typeof size === 'number' ? size : spacing[size]
  }),

  marginVertical: (size: keyof Spacing | number) => ({
    marginVertical: typeof size === 'number' ? size : spacing[size]
  }),

  padding: (size: keyof Spacing | number) => ({
    padding: typeof size === 'number' ? size : spacing[size]
  }),

  paddingTop: (size: keyof Spacing | number) => ({
    paddingTop: typeof size === 'number' ? size : spacing[size]
  }),

  paddingBottom: (size: keyof Spacing | number) => ({
    paddingBottom: typeof size === 'number' ? size : spacing[size]
  }),

  paddingHorizontal: (size: keyof Spacing | number) => ({
    paddingHorizontal: typeof size === 'number' ? size : spacing[size]
  }),

  paddingVertical: (size: keyof Spacing | number) => ({
    paddingVertical: typeof size === 'number' ? size : spacing[size]
  }),

  /**
   * Check if color is light or dark
   */
  isLightColor: (color: string): boolean => {
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000
    return brightness > 155
  },

  /**
   * Create responsive size based on screen width
   */
  responsiveSize: (base: number, factor: number = 0.1): number => {
    return base + (screenWidth - 375) * factor
  },

  /**
   * Clamp value between min and max
   */
  clamp: (value: number, min: number, max: number): number => {
    return Math.min(Math.max(value, min), max)
  }
}

export default theme