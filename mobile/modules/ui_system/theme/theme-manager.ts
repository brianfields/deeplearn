/**
 * Theme Manager for React Native Learning App
 *
 * Manages theme state, persistence, and switching between light/dark modes
 */

import { Platform } from 'react-native';
import { tokens } from '../tokens';

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

// Light theme colors mapped from Weimar Edge tokens
const lightColors: ThemeColors = {
  primary: tokens.color.accent600,
  secondary: tokens.color.gilt500,
  accent: tokens.color.accent400,
  background: tokens.color.paper0,
  surface: '#FFFFFF',
  text: tokens.color.ink900,
  textSecondary: tokens.color.accent200,
  border: tokens.color.accent200,
  success: tokens.color.emerald500,
  warning: tokens.color.amber600,
  error: tokens.color.rouge600,
  info: tokens.color.sky500,
};

// Dark theme colors (approximation using tokens; app uses single theme but keep parity)
const darkColors: ThemeColors = {
  primary: tokens.color.accent400,
  secondary: tokens.color.gilt500,
  accent: tokens.color.sky500,
  background: '#1A1A1A',
  surface: '#2D2D2D',
  text: '#FFFFFF',
  textSecondary: '#B0B0B0',
  border: '#404040',
  success: tokens.color.emerald500,
  warning: tokens.color.amber600,
  error: tokens.color.rouge600,
  info: tokens.color.sky500,
};

// Shared spacing derived from tokens
const spacing: Spacing = {
  xs: tokens.space[1],
  sm: tokens.space[2],
  md: tokens.space[4],
  lg: tokens.space[6],
  xl: tokens.space[8],
  xxl: tokens.space[10],
};

// Shared typography derived from tokens
const typography: Typography = {
  heading1: {
    fontSize: tokens.type.h1.size,
    fontWeight: Platform.OS === 'ios' ? tokens.type.h1.weight : 'bold',
    lineHeight: tokens.type.h1.line,
  },
  heading2: {
    fontSize: tokens.type.h2.size,
    fontWeight: Platform.OS === 'ios' ? tokens.type.h2.weight : 'bold',
    lineHeight: tokens.type.h2.line,
  },
  heading3: {
    fontSize: tokens.type.title.size,
    fontWeight: Platform.OS === 'ios' ? tokens.type.title.weight : 'bold',
    lineHeight: tokens.type.title.line,
  },
  body: {
    fontSize: tokens.type.body.size,
    fontWeight: Platform.OS === 'ios' ? tokens.type.body.weight : 'normal',
    lineHeight: tokens.type.body.line,
  },
  caption: {
    fontSize: tokens.type.caption.size,
    fontWeight: Platform.OS === 'ios' ? tokens.type.caption.weight : 'normal',
    lineHeight: tokens.type.caption.line,
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
