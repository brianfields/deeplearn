/**
 * UI System Service
 *
 * Manages theme state, component utilities, and design system logic.
 * Returns DTOs only, never raw theme objects.
 */

import {
  theme,
  colors,
  spacing,
  typography,
  responsive,
  shadows,
  animations,
  utils,
  commonStyles,
} from './theme/theme';
import type {
  Theme,
  ThemeManagerState,
  DesignSystemConfig,
  ResponsiveConfig,
  AnimationConfig,
  UtilityFunctions,
} from './models';

export class UISystemService {
  private themeState: ThemeManagerState;

  constructor() {
    this.themeState = {
      currentTheme: theme,
      isDarkMode: false,
      systemTheme: 'auto',
    };
  }

  // Theme Management
  getCurrentTheme(): Theme {
    return this.themeState.currentTheme;
  }

  getThemeState(): ThemeManagerState {
    return { ...this.themeState };
  }

  setDarkMode(enabled: boolean): void {
    this.themeState.isDarkMode = enabled;
    // In a real implementation, you'd switch between light/dark themes here
    // For now, we only have one theme
  }

  setSystemTheme(mode: 'light' | 'dark' | 'auto'): void {
    this.themeState.systemTheme = mode;

    if (mode === 'auto') {
      // In a real implementation, you'd detect system theme here
      // For now, default to light
      this.themeState.isDarkMode = false;
    } else {
      this.themeState.isDarkMode = mode === 'dark';
    }
  }

  // Design System Access
  getDesignSystem(): DesignSystemConfig {
    return {
      theme: this.getCurrentTheme(),
      responsive,
      shadows,
      animations,
      utils,
    };
  }

  // Component Utilities
  getCommonStyles(): typeof commonStyles {
    return commonStyles;
  }

  // Responsive Utilities
  getResponsiveConfig(): ResponsiveConfig {
    return responsive;
  }

  isSmallScreen(): boolean {
    return responsive.isSmallScreen;
  }

  isMediumScreen(): boolean {
    return responsive.isMediumScreen;
  }

  isLargeScreen(): boolean {
    return responsive.isLargeScreen;
  }

  // Utility Functions
  getUtils(): UtilityFunctions {
    return utils;
  }

  // Spacing Utilities
  getSpacing(size: keyof typeof spacing): number {
    return spacing[size];
  }

  // Color Utilities
  getColor(colorName: keyof typeof colors): string {
    return colors[colorName];
  }

  isLightColor(color: string): boolean {
    return utils.isLightColor(color);
  }

  // Typography Utilities
  getTypography(
    style: keyof typeof typography
  ): (typeof typography)[keyof typeof typography] {
    return typography[style];
  }

  // Shadow Utilities
  getShadow(size: keyof typeof shadows): any {
    return shadows[size];
  }

  // Animation Utilities
  getAnimationDuration(
    speed: keyof Pick<AnimationConfig, 'fast' | 'normal' | 'slow'>
  ): number {
    return animations[speed];
  }

  getAnimationEasing(
    type: keyof Pick<AnimationConfig, 'easeIn' | 'easeOut' | 'easeInOut'>
  ): string {
    return animations[type];
  }
}
