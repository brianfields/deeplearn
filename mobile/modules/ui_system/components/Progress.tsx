/**
 * Progress Component for React Native Learning App
 *
 * Animated progress bar with customizable styling
 */

import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { internalUiSystemProvider } from '../internalProvider';
import type { ProgressProps } from '../models';
import { animationTimings } from '../utils/animations';
import { reducedMotion } from '../utils/motion';
import { tokens } from '../tokens';

const uiSystemProvider = internalUiSystemProvider;

export const Progress: React.FC<ProgressProps> = ({
  progress,
  size = 'medium',
  color,
  backgroundColor,
  showLabel = false,
  label,
  animated = true,
  style,
}) => {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const progressWidth = useSharedValue(0);
  const prevProgressRef = useRef<number>(0);

  const defaultColor = color || theme.colors.primary;
  const defaultBackgroundColor = backgroundColor || theme.colors.border;

  const height = size === 'small' ? 4 : size === 'large' ? 12 : 8;

  useEffect(() => {
    const targetWidth = Math.max(0, Math.min(100, progress));
    const previous = prevProgressRef.current;
    const delta = Math.abs(targetWidth - previous);

    if (animated && !reducedMotion.enabled) {
      const duration =
        delta <= 12 ? animationTimings.micro : animationTimings.ui;
      progressWidth.value = withTiming(targetWidth, {
        duration,
        easing: Easing.bezier(0.2, 0.8, 0.2, 1),
      });
    } else {
      progressWidth.value = targetWidth;
    }

    prevProgressRef.current = targetWidth;
  }, [progress, animated]); // eslint-disable-line react-hooks/exhaustive-deps

  const animatedStyle = useAnimatedStyle(() => ({
    width: `${progressWidth.value}%`,
  }));

  // Apply incoming style to wrapper so width/flex take effect
  const flattenedStyle = StyleSheet.flatten(style) || {};
  const { pointerEvents, ...wrapperStyle } = flattenedStyle as any;

  const containerStyle = StyleSheet.flatten([
    styles.container,
    {
      height,
      backgroundColor: defaultBackgroundColor,
      width: '100%' as const,
      borderRadius: tokens.radius.sm,
      overflow: 'hidden' as const,
    },
  ]) as React.ComponentProps<typeof View>['style'];

  // On web, pointerEvents should be passed via style to avoid deprecation
  const wrapperWithPointerEvents =
    pointerEvents !== undefined
      ? ({ ...wrapperStyle, pointerEvents } as any)
      : wrapperStyle;

  return (
    <View style={wrapperWithPointerEvents}>
      {showLabel && (
        <Text
          style={[
            // Ensure proper RN TextStyle typing for caption label
            {
              ...theme.typography.caption,
              color: theme.colors.textSecondary,
              textAlign: 'right' as const,
              marginBottom: 4,
            } as any,
          ]}
        >
          {label || `${Math.round(progress)}%`}
        </Text>
      )}
      <View
        style={containerStyle}
        accessibilityRole="progressbar"
        accessibilityValue={{
          min: 0,
          max: 100,
          now: Math.round(Math.max(0, Math.min(100, progress))),
        }}
      >
        <Animated.View
          style={[
            styles.progress,
            {
              backgroundColor: defaultColor,
              height,
              borderRadius: tokens.radius.sm,
            },
            animatedStyle,
          ]}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 4,
    overflow: 'hidden',
  },
  progress: {
    borderRadius: 4,
  },
  label: {
    // unused; label styling now derives from theme.typography.caption
  },
});

export default Progress;
