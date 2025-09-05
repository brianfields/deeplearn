/**
 * Theme API for Infrastructure module
 *
 * Provides theme management functionality to other modules
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  ThemeManager,
  defaultThemeManager,
  lightTheme,
  darkTheme,
  Theme,
} from '../theme/theme-manager';

const THEME_STORAGE_KEY = '@theme_preference';

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
  themeManager?: ThemeManager;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  themeManager = defaultThemeManager,
}) => {
  const [theme, setThemeState] = useState<Theme>(themeManager.getTheme());

  useEffect(() => {
    // Load saved theme preference
    const loadThemePreference = async () => {
      try {
        const savedTheme = await AsyncStorage.getItem(THEME_STORAGE_KEY);
        if (savedTheme) {
          const themeMode = JSON.parse(savedTheme);
          const theme = themeMode === 'dark' ? darkTheme : lightTheme;
          themeManager.setTheme(theme);
        }
      } catch (error) {
        console.warn('Failed to load theme preference:', error);
      }
    };

    loadThemePreference();

    // Listen for theme changes
    const handleThemeChange = (newTheme: Theme) => {
      setThemeState(newTheme);
      saveThemePreference(newTheme);
    };

    themeManager.addListener(handleThemeChange);

    return () => {
      themeManager.removeListener(handleThemeChange);
    };
  }, [themeManager]);

  const saveThemePreference = async (theme: Theme) => {
    try {
      await AsyncStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(theme.mode));
    } catch (error) {
      console.warn('Failed to save theme preference:', error);
    }
  };

  const setTheme = (newTheme: Theme) => {
    themeManager.setTheme(newTheme);
  };

  const toggleTheme = () => {
    themeManager.toggleTheme();
  };

  const contextValue: ThemeContextValue = {
    theme,
    setTheme,
    toggleTheme,
    isDark: theme.mode === 'dark',
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Re-export theme types and presets
export type {
  Theme,
  ThemeColors,
  Spacing,
  Typography,
} from '../theme/theme-manager';
export { lightTheme, darkTheme } from '../theme/theme-manager';
