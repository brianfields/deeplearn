/**
 * LessonCard component for displaying lesson summaries.
 *
 * A reusable card component that shows lesson information in a touch-friendly format.
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';
import {
  BookOpen,
  Clock,
  Target,
  CheckCircle,
  ArrowRight,
  WifiOff,
  Headphones,
} from 'lucide-react-native';

import { LessonSummary } from '../models';
import { uiSystemProvider, Text, useHaptics } from '../../ui_system/public';
import { layoutStyles } from '../../ui_system/styles/layout';
import { spacingPatterns } from '../../ui_system/styles/spacing';

interface LessonCardProps {
  lesson: LessonSummary;
  onPress: (lesson: LessonSummary) => void;
  isOfflineAvailable?: boolean;
  showProgress?: boolean;
  progressPercentage?: number;
  index?: number;
  unitTitle?: string; // optional unit context
}

export function LessonCard({
  lesson,
  onPress,
  isOfflineAvailable = true,
  showProgress = false,
  progressPercentage = 0,
  index,
  unitTitle,
}: LessonCardProps) {
  const scaleValue = useSharedValue(1);
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const spacing = spacingPatterns();

  const handlePressIn = () => {
    scaleValue.value = withSpring(0.98);
  };

  const handlePressOut = () => {
    scaleValue.value = withSpring(1);
  };

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scaleValue.value }],
  }));

  const handlePress = () => {
    haptics.trigger('light');
    onPress(lesson);
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={0.8}
      style={styles.container}
      testID={index !== undefined ? `lesson-card-${index}` : undefined}
    >
      <Animated.View
        style={[
          styles.card,
          animatedStyle,
          {
            backgroundColor: theme.colors.surface,
            padding: ui.getSpacing('md'),
            // Raised elevation per Weimar Edge
            ...(ui.getDesignSystem().shadows.medium as any),
          },
          layoutStyles.radiusMd,
        ]}
      >
        <View style={styles.header}>
          <View style={styles.lessonInfo}>
            <Text
              variant="title"
              weight="700"
              color={theme.colors.text}
              numberOfLines={2}
              style={spacing.marginBottom4}
            >
              {lesson.title}
            </Text>
            {/* coreConcept removed in new model; keep spacer */}
            {unitTitle && (
              <View
                style={[
                  layoutStyles.selfStart,
                  spacing.marginTop6,
                  {
                    backgroundColor: theme.colors.border,
                  },
                  layoutStyles.radiusSm,
                  spacing.paddingVertical6Horizontal8,
                ]}
              >
                <Text
                  variant="caption"
                  numberOfLines={1}
                  weight="600"
                  color={theme.colors.text}
                >
                  {unitTitle}
                </Text>
              </View>
            )}
          </View>

          <View style={styles.meta}>
            {lesson.hasPodcast && (
              <Headphones
                size={16}
                color={theme.colors.textSecondary}
                style={spacing.marginRight6}
                accessibilityLabel="Lesson podcast available"
              />
            )}
            {!isOfflineAvailable && (
              <WifiOff size={16} color={theme.colors.textSecondary} />
            )}
            <ArrowRight size={20} color={theme.colors.textSecondary} />
          </View>
        </View>

        <View style={styles.details}>
          <View style={styles.detailItem}>
            <Clock size={14} color={theme.colors.textSecondary} />
            <Text variant="caption" color={theme.colors.textSecondary}>
              {lesson.durationDisplay}
            </Text>
          </View>

          <View style={styles.detailItem}>
            <Target size={14} color={theme.colors.textSecondary} />
            <Text variant="caption" color={theme.colors.textSecondary}>
              {lesson.learnerLevelLabel}
            </Text>
          </View>

          <View style={styles.detailItem}>
            <BookOpen size={14} color={theme.colors.textSecondary} />
            <Text variant="caption" color={theme.colors.textSecondary}>
              {lesson.componentCount} exercises
            </Text>
          </View>

          {lesson.isReadyForLearning && (
            <View style={styles.detailItem}>
              <CheckCircle size={14} color={theme.colors.success} />
              <Text variant="caption" color={theme.colors.success} weight="500">
                Ready
              </Text>
            </View>
          )}
        </View>

        {showProgress && progressPercentage > 0 && (
          <View style={spacing.marginBottom8}>
            <View style={styles.progressContainer}>
              <View
                style={[
                  styles.progressBar,
                  {
                    backgroundColor: theme.colors.primary,
                    width: `${progressPercentage}%`,
                  },
                ]}
              />
            </View>
            <Text variant="caption" color={theme.colors.textSecondary}>
              {Math.round(progressPercentage)}% complete
            </Text>
          </View>
        )}

        <View style={styles.tags}>
          {lesson.tags.slice(0, 3).map((tag, index) => (
            <View
              key={index}
              style={[
                {
                  backgroundColor: theme.colors.border,
                },
                layoutStyles.radiusSm,
                spacing.paddingVertical6Horizontal8,
              ]}
            >
              <Text variant="caption" color={theme.colors.text} weight="500">
                {tag}
              </Text>
            </View>
          ))}
        </View>
      </Animated.View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
  },
  card: {
    overflow: 'hidden' as const,
  },
  header: {
    flexDirection: 'row' as const,
    justifyContent: 'space-between' as const,
    alignItems: 'flex-start' as const,
    marginBottom: 12,
  },
  lessonInfo: {
    flex: 1,
  },
  meta: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    gap: 8,
    marginLeft: 8,
    flexShrink: 0,
  },
  details: {
    flexDirection: 'row' as const,
    gap: 12,
    marginBottom: 12,
    flexWrap: 'wrap' as const,
  },
  detailItem: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    gap: 4,
  },
  progressContainer: {
    height: 4,
    borderRadius: 2,
    marginBottom: 4,
    overflow: 'hidden' as const,
  },
  progressBar: {
    height: '100%' as const,
    borderRadius: 2,
  },
  tags: {
    flexDirection: 'row' as const,
    gap: 8,
    flexWrap: 'wrap' as const,
  },
});
