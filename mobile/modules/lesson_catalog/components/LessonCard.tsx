/**
 * LessonCard component for displaying lesson summaries.
 *
 * A reusable card component that shows lesson information in a touch-friendly format.
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
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

interface LessonCardProps {
  lesson: LessonSummary;
  onPress: (lesson: LessonSummary) => void;
  isOfflineAvailable?: boolean;
  showProgress?: boolean;
  progressPercentage?: number;
}

export function LessonCard({
  lesson,
  onPress,
  isOfflineAvailable = true,
  showProgress = false,
  progressPercentage = 0,
}: LessonCardProps) {
  const scaleValue = useSharedValue(1);

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
    onPress(lesson);
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={0.8}
      style={styles.container}
    >
      <Animated.View style={[styles.card, animatedStyle]}>
        <View style={styles.header}>
          <View style={styles.lessonInfo}>
            <Text style={styles.title} numberOfLines={2}>
              {lesson.title}
            </Text>
            <Text style={styles.description} numberOfLines={2}>
              {lesson.coreConcept}
            </Text>
          </View>

          <View style={styles.meta}>
            {!isOfflineAvailable && <WifiOff size={16} color="#6B7280" />}
            <ArrowRight size={20} color="#6B7280" />
          </View>
        </View>

        <View style={styles.details}>
          <View style={styles.detailItem}>
            <Clock size={14} color="#6B7280" />
            <Text style={styles.detailText}>{lesson.durationDisplay}</Text>
          </View>

          <View style={styles.detailItem}>
            <Target size={14} color="#6B7280" />
            <Text style={styles.detailText}>{lesson.difficultyLevel}</Text>
          </View>

          <View style={styles.detailItem}>
            <BookOpen size={14} color="#6B7280" />
            <Text style={styles.detailText}>
              {lesson.componentCount} components
            </Text>
          </View>

          {lesson.isReadyForLearning && (
            <View style={styles.detailItem}>
              <CheckCircle size={14} color="#10B981" />
              <Text style={[styles.detailText, styles.readyText]}>Ready</Text>
            </View>
          )}
        </View>

        {showProgress && progressPercentage > 0 && (
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${progressPercentage}%` },
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              {Math.round(progressPercentage)}% complete
            </Text>
          </View>
        )}

        <View style={styles.tags}>
          {lesson.tags.slice(0, 3).map((tag, index) => (
            <View key={index} style={styles.tag}>
              <Text style={styles.tagText}>{tag}</Text>
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
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
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
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  description: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
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
  detailText: {
    fontSize: 12,
    color: '#6B7280',
  },
  readyText: {
    color: '#10B981',
    fontWeight: '500',
  },
  progressContainer: {
    marginBottom: 12,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'right',
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  tagText: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '500',
  },
});
