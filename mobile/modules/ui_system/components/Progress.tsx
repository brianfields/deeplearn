/**
 * Progress Component for React Native Learning App
 *
 * Animated progress bar with customizable styling
 */

import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';
import { uiSystemProvider } from '../public';
import type { ProgressProps } from '../models';

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

  const defaultColor = color || theme.colors.primary;
  const defaultBackgroundColor = backgroundColor || theme.colors.border;

  const height = size === 'small' ? 4 : size === 'large' ? 12 : 8;

  useEffect(() => {
    const targetWidth = Math.max(0, Math.min(100, progress));

    if (animated) {
      progressWidth.value = withSpring(targetWidth, {
        damping: 15,
        stiffness: 150,
      });
    } else {
      progressWidth.value = targetWidth;
    }
  }, [progress, animated]); // eslint-disable-line react-hooks/exhaustive-deps

  const animatedStyle = useAnimatedStyle(() => ({
    width: `${progressWidth.value}%`,
  }));

  // Separate pointerEvents from style to avoid deprecation warning
  const { pointerEvents, ...otherStyles } = style || {};

  const containerStyle = [
    styles.container,
    {
      height,
      backgroundColor: defaultBackgroundColor,
    },
    otherStyles,
    pointerEvents && { pointerEvents },
  ];

  return (
    <View>
      {showLabel && (
        <Text style={[styles.label, { color: theme.colors.text }]}>
          {label || `${Math.round(progress)}%`}
        </Text>
      )}
      <View style={containerStyle}>
        <Animated.View
          style={[
            styles.progress,
            { backgroundColor: defaultColor, height },
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
    fontSize: 12,
    marginBottom: 4,
    textAlign: 'right',
  },
});

export default Progress;
