/**
 * Navigation Options Utility
 *
 * Provides consistent screen option configurations for different navigation types.
 * This ensures semantic consistency across the app:
 * - Stack screens: slide right (forward), slide left (back)
 * - Modal screens: slide up, swipe down to dismiss
 * - Detail cards: slide up, similar to modals but with card presentation
 */

import type { NativeStackNavigationOptions } from '@react-navigation/native-stack';
import { Easing } from 'react-native';
import { reducedMotion } from '../modules/ui_system/utils/motion';

export type ScreenType = 'stack' | 'modal' | 'detail' | 'locked';

/**
 * Transition timing configuration - used for both forward and back animations
 */
const transitionSpec = {
  open: {
    animation: 'timing' as const,
    config: {
      duration: 220,
      easing: Easing.inOut(Easing.ease),
      useNativeDriver: false,
    },
  },
  close: {
    animation: 'timing' as const,
    config: {
      duration: 220,
      easing: Easing.inOut(Easing.ease),
      useNativeDriver: false,
    },
  },
};

/**
 * Card style animation - slides from right on open, slides to left on close
 * This provides semantic back animation where previous screen slides in from left
 */
const cardStyleInterpolator = ({
  current,
  next: _next,
  layouts,
}: {
  current: any;
  next?: any;
  layouts: any;
}): any => {
  return {
    cardStyle: {
      transform: [
        {
          translateX: current.progress.interpolate({
            inputRange: [0, 1],
            outputRange: [layouts.screen.width, 0],
          }),
        },
      ],
    },
    overlayStyle: {
      opacity: current.progress.interpolate({
        inputRange: [0, 1],
        outputRange: [0, 0.07],
      }),
    },
  };
};

/**
 * Get standard screen options based on screen type
 *
 * @param type - The type of screen presentation
 * @returns Screen options with appropriate animations and gestures
 *
 * @example
 * <LearningStack.Screen
 *   name="UnitDetail"
 *   component={UnitDetailScreen}
 *   options={getScreenOptions('stack')}
 * />
 */
export function getScreenOptions(
  type: ScreenType
): NativeStackNavigationOptions {
  const noAnimation = reducedMotion.enabled ? 'none' : undefined;

  switch (type) {
    case 'stack':
      // Standard forward navigation: slide in from right, swipe left to go back
      // Back animation: previous screen slides in from left (via cardStyleInterpolator)
      return {
        animation: noAnimation || 'slide_from_right',
        gestureDirection: 'horizontal',
        headerShown: false,
        ...(reducedMotion.enabled
          ? {}
          : {
              transitionSpec,
              cardStyleInterpolator,
            }),
      };

    case 'modal':
      // Modal presentation: slide in from bottom, swipe down to dismiss
      return {
        presentation: 'modal',
        animation: noAnimation || 'slide_from_bottom',
        gestureDirection: 'vertical',
        headerShown: false,
      };

    case 'detail':
      // Card presentation (iOS): slide in from bottom, shows underlying screen
      return {
        presentation: 'card',
        animation: noAnimation || 'slide_from_bottom',
        gestureDirection: 'vertical',
        headerShown: false,
      };

    case 'locked':
      // No gestures allowed (e.g., during learning session)
      return {
        gestureEnabled: false,
        headerShown: false,
      };

    default:
      return { headerShown: false };
  }
}

/**
 * Merge custom options with screen type defaults
 *
 * @param type - The base screen type
 * @param customOptions - Additional options to merge
 * @returns Merged options with type defaults as base
 */
export function mergeScreenOptions(
  type: ScreenType,
  customOptions?: Partial<NativeStackNavigationOptions>
): NativeStackNavigationOptions {
  return {
    ...getScreenOptions(type),
    ...customOptions,
  };
}
