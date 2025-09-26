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
} from 'lucide-react-native';

import { LessonSummary } from '../models';
import { uiSystemProvider, Text, useHaptics } from '../../ui_system/public';

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
            borderRadius: 12,
            padding: ui.getSpacing('md'),
            // Raised elevation per Weimar Edge
            ...(ui.getDesignSystem().shadows.medium as any),
          },
        ]}
      >
        <View style={styles.header}>
          <View style={styles.lessonInfo}>
            <Text
              variant="title"
              weight="700"
              color={theme.colors.text}
              numberOfLines={2}
              style={{ marginBottom: 4 }}
            >
              {lesson.title}
            </Text>
            {/* coreConcept removed in new model; keep spacer */}
            {unitTitle && (
              <View
                style={{
                  alignSelf: 'flex-start',
                  marginTop: 6,
                  backgroundColor: theme.colors.border,
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: 6,
                }}
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
          <View style={{ marginBottom: ui.getSpacing('sm') }}>
            <View
              style={{
                height: 4,
                backgroundColor: theme.colors.border,
                borderRadius: 2,
                marginBottom: 4,
              }}
            >
              <View
                style={{
                  height: '100%',
                  backgroundColor: theme.colors.primary,
                  borderRadius: 2,
                  width: `${progressPercentage}%`,
                }}
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
              style={{
                backgroundColor: theme.colors.border,
                paddingHorizontal: 8,
                paddingVertical: 4,
                borderRadius: 6,
              }}
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
    marginBottom: 16,
  },
  card: {
    // colors and elevation pulled from theme dynamically
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  lessonInfo: {
    flex: 1,
    marginRight: 12,
  },
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  details: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    marginBottom: 12,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
});
