/**
 * UI System Public Interface
 *
 * The only interface other modules should import from.
 * Pure forwarder - no logic, just selects/forwards service methods.
 */

import { UISystemService } from './service';
import type {
  Theme,
  ThemeColors,
  Spacing,
  ThemeManagerState,
  DesignSystemConfig,
} from './models';

// Re-export UI components (direct exports - no provider needed)
export { Button } from './components/Button';
export { Card } from './components/Card';
export { Progress } from './components/Progress';
export { ArtworkImage } from './components/ArtworkImage';
export { Slider } from './components/Slider';
export { Box } from './components/primitives/Box';
export { Text } from './components/primitives/Text';
export { useHaptics } from './hooks/useHaptics';

// Public interface protocol (for theme management)
export interface UISystemProvider {
  getCurrentTheme(): Theme;
  getThemeState(): ThemeManagerState;
  setDarkMode(enabled: boolean): void;
  setSystemTheme(mode: 'light' | 'dark' | 'auto'): void;
  getDesignSystem(): DesignSystemConfig;
  isSmallScreen(): boolean;
  isMediumScreen(): boolean;
  isLargeScreen(): boolean;
  getSpacing(size: keyof Spacing): number;
  getColor(colorName: keyof ThemeColors): string;
  isLightColor(color: string): boolean;
}

// Service instance (singleton)
let serviceInstance: UISystemService | null = null;

function getServiceInstance(): UISystemService {
  if (!serviceInstance) {
    serviceInstance = new UISystemService();
  }
  return serviceInstance;
}

// Public provider function (for theme management)
export function uiSystemProvider(): UISystemProvider {
  const service = getServiceInstance();

  // Pure forwarder - no logic
  return {
    getCurrentTheme: service.getCurrentTheme.bind(service),
    getThemeState: service.getThemeState.bind(service),
    setDarkMode: service.setDarkMode.bind(service),
    setSystemTheme: service.setSystemTheme.bind(service),
    getDesignSystem: service.getDesignSystem.bind(service),
    isSmallScreen: service.isSmallScreen.bind(service),
    isMediumScreen: service.isMediumScreen.bind(service),
    isLargeScreen: service.isLargeScreen.bind(service),
    getSpacing: service.getSpacing.bind(service),
    getColor: service.getColor.bind(service),
    isLightColor: service.isLightColor.bind(service),
  };
}

// Export types for other modules
export type {
  Theme,
  ThemeColors,
  Typography,
  Spacing,
  ButtonProps,
  CardProps,
  ProgressProps,
  ArtworkImageProps,
  SliderProps,
  ThemeManagerState,
  DesignSystemConfig,
} from './models';
