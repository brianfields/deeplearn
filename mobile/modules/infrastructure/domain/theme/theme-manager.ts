/**
 * Theme Manager for React Native Learning App
 *
 * Manages theme state, persistence, and switching between light/dark modes
 */

import { Platform } from 'react-native';

export interface ThemeColors {
  // Primary colors
  primary: string;
  secondary: string;
  accent: string;

  // Background colors
  background: string;
  surface: string;

  // Text colors
  text: string;
  textSecondary: string;

  // UI colors
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
  mode: 'light' | 'dark';
  colors: ThemeColors;
  spacing: Spacing;
  typography: Typography;
  shadows?: any;
}

// Light theme colors
const lightColors: ThemeColors = {
  primary: '#1CB0F6',
  secondary: '#00CD9C',
  accent: '#FF9600',
  background: '#F7F8FA',
  surface: '#FFFFFF',
  text: '#2B2D42',
  textSecondary: '#5E6B73',
  border: '#E5E7EB',
  success: '#22C55E',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
};

// Dark theme colors
const darkColors: ThemeColors = {
  primary: '#1CB0F6',
  secondary: '#00CD9C',
  accent: '#FF9600',
  background: '#1A1A1A',
  surface: '#2D2D2D',
  text: '#FFFFFF',
  textSecondary: '#B0B0B0',
  border: '#404040',
  success: '#22C55E',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
};

// Shared spacing
const spacing: Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

// Shared typography
const typography: Typography = {
  heading1: {
    fontSize: 32,
    fontWeight: Platform.OS === 'ios' ? '700' : 'bold',
    lineHeight: 40,
  },
  heading2: {
    fontSize: 24,
    fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
    lineHeight: 32,
  },
  heading3: {
    fontSize: 20,
    fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
    lineHeight: 28,
  },
  body: {
    fontSize: 16,
    fontWeight: Platform.OS === 'ios' ? '400' : 'normal',
    lineHeight: 24,
  },
  caption: {
    fontSize: 14,
    fontWeight: Platform.OS === 'ios' ? '400' : 'normal',
    lineHeight: 20,
  },
};

// Shadow styles
const shadows = {
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

// Light theme
export const lightTheme: Theme = {
  mode: 'light',
  colors: lightColors,
  spacing,
  typography,
  shadows,
};

// Dark theme
export const darkTheme: Theme = {
  mode: 'dark',
  colors: darkColors,
  spacing,
  typography,
  shadows,
};

export type ThemeChangeListener = (theme: Theme) => void;

export class ThemeManager {
  private currentTheme: Theme;
  private listeners: ThemeChangeListener[];

  constructor(initialTheme: Theme = lightTheme) {
    this.currentTheme = initialTheme;
    this.listeners = [];
  }

  getTheme(): Theme {
    return this.currentTheme;
  }

  setTheme(theme: Theme): void {
    this.currentTheme = theme;
    this.notifyListeners(theme);
  }

  toggleTheme(): void {
    const newTheme =
      this.currentTheme.mode === 'light' ? darkTheme : lightTheme;
    this.setTheme(newTheme);
  }

  addListener(listener: ThemeChangeListener): void {
    this.listeners.push(listener);
  }

  removeListener(listener: ThemeChangeListener): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  private notifyListeners(theme: Theme): void {
    this.listeners.forEach(listener => listener(theme));
  }
}

// Default theme manager instance
export const defaultThemeManager = new ThemeManager();
