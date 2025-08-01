/**
 * Progress Component for React Native Learning App
 *
 * Animated progress bar with customizable styling
 */

import React, { useEffect } from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  withSpring,
} from 'react-native-reanimated';
import { colors } from '@/utils/theme';

interface ProgressProps {
  value: number; // 0-100
  style?: ViewStyle;
  height?: number;
  color?: string;
  backgroundColor?: string;
  animated?: boolean;
  animationType?: 'timing' | 'spring';
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  style,
  height = 8,
  color = colors.primary,
  backgroundColor = colors.border,
  animated = true,
  animationType = 'spring',
}) => {
  const progressWidth = useSharedValue(0);

  useEffect(() => {
    const targetWidth = Math.max(0, Math.min(100, value));

    if (animated) {
      if (animationType === 'spring') {
        progressWidth.value = withSpring(targetWidth, {
          damping: 15,
          stiffness: 150,
        });
      } else {
        progressWidth.value = withTiming(targetWidth, {
          duration: 500,
        });
      }
    } else {
      progressWidth.value = targetWidth;
    }
  }, [value, animated, animationType]); // eslint-disable-line react-hooks/exhaustive-deps

  const animatedStyle = useAnimatedStyle(() => ({
    width: `${progressWidth.value}%`,
  }));

  const containerStyle = [styles.container, { height, backgroundColor }, style];

  return (
    <View style={containerStyle}>
      <Animated.View
        style={[
          styles.progress,
          { backgroundColor: color, height },
          animatedStyle,
        ]}
      />
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
});

export default Progress;
