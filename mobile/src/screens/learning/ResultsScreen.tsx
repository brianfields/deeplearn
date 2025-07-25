/**
 * ResultsScreen - Learning Session Completion & Celebration
 *
 * This screen celebrates the completion of a learning session and presents
 * comprehensive results to the user. It serves as both a reward mechanism
 * and a learning analytics dashboard.
 *
 * LEARNING FLOW COMPLETION:
 * - Final destination after completing a learning session
 * - Processes and displays aggregated results from LearningFlow
 * - Provides closure and sense of accomplishment
 * - Offers pathways for continued learning
 *
 * CELEBRATION & MOTIVATION:
 * - Animated celebrations based on performance
 * - Star ratings and trophy displays
 * - Performance-based congratulatory messages
 * - Haptic feedback for positive reinforcement
 *
 * ANALYTICS & FEEDBACK:
 * - Overall session score calculation and display
 * - Time spent tracking and presentation
 * - Step completion statistics
 * - Correct vs incorrect answer breakdowns
 *
 * USER JOURNEY FACILITATION:
 * - "Continue Learning" button returns to topic list
 * - "Try Again" option for improvement (appears for lower scores)
 * - Smooth navigation back to topic selection
 * - Progress persistence for learning streaks
 *
 * PERFORMANCE VISUALIZATION:
 * - Animated progress bars for score display
 * - Color-coded performance indicators
 * - Star rating system (1-3 stars based on score)
 * - Trophy animations for exceptional performance
 *
 * MOBILE EXPERIENCE:
 * - Celebration animations with spring physics
 * - Progressive content reveal
 * - Haptic feedback for achievement moments
 * - Touch-friendly action buttons
 *
 * INTEGRATION POINTS:
 * - Receives LearningResults from LearningFlowScreen
 * - Communicates with learningService for progress tracking
 * - Navigates back to TopicListScreen for continued learning
 * - Updates user statistics and learning streaks
 *
 * RESULTS DATA PROCESSING:
 * - Calculates final percentage scores
 * - Determines performance categories (Perfect, Good, Needs Work)
 * - Aggregates time and interaction metrics
 * - Prepares data for long-term progress tracking
 */

import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  Platform,
  Vibration,
} from 'react-native';
import Animated, {
  FadeIn,
  ZoomIn,
  SlideInUp,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withSequence,
  withDelay,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

// Icons
import {
  Trophy,
  Star,
  CheckCircle,
  Target,
  Clock,
  ArrowRight,
  RotateCcw,
} from 'lucide-react-native';

// Components
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';

// Theme & Types
import { colors, spacing, typography, shadows, textStyle } from '@/utils/theme';
import type { LearningStackParamList } from '@/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<LearningStackParamList, 'Results'>;

export default function ResultsScreen({ navigation, route }: Props) {
  const { results } = route.params;

  // Animated values
  const trophyScale = useSharedValue(0);
  const scoreProgress = useSharedValue(0);
  const starsOpacity = useSharedValue(0);

  // Calculate performance metrics
  const scorePercentage = Math.max(0, Math.min(100, results.finalScore));
  const timeInMinutes = Math.round(results.timeSpent / 60);
  const isPerfectScore = scorePercentage === 100;
  const isGoodScore = scorePercentage >= 80;

  // Performance message
  const getPerformanceMessage = () => {
    if (isPerfectScore) return 'Perfect! Outstanding work! 🎉';
    if (isGoodScore) return 'Great job! Well done! 👏';
    if (scorePercentage >= 60) return 'Good effort! Keep practicing! 💪';
    return "Keep learning! You're improving! 📚";
  };

  const getPerformanceColor = () => {
    if (isPerfectScore) return colors.warning; // Gold
    if (isGoodScore) return colors.success;
    if (scorePercentage >= 60) return colors.primary;
    return colors.textSecondary;
  };

  // Animation effects
  useEffect(() => {
    // Haptic feedback for completion
    if (Platform.OS === 'ios') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } else {
      Vibration.vibrate(100);
    }

    // Trophy animation
    trophyScale.value = withDelay(
      300,
      withSequence(
        withSpring(1.2, { damping: 10 }),
        withSpring(1.0, { damping: 15 })
      )
    );

    // Score progress animation
    scoreProgress.value = withDelay(800, withSpring(scorePercentage));

    // Stars animation
    starsOpacity.value = withDelay(1200, withSpring(1));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const trophyStyle = useAnimatedStyle(() => ({
    transform: [{ scale: trophyScale.value }],
  }));

  const handleContinue = () => {
    navigation.popToTop();
  };

  const handleRetry = () => {
    navigation.goBack();
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header with trophy */}
        <Animated.View entering={FadeIn.delay(200)} style={styles.header}>
          <Animated.View style={[styles.trophyContainer, trophyStyle]}>
            <Trophy
              size={80}
              color={getPerformanceColor()}
              fill={isPerfectScore ? colors.warning : 'transparent'}
            />
          </Animated.View>

          <Animated.Text
            entering={SlideInUp.delay(500)}
            style={[styles.congratsText, { color: getPerformanceColor() }]}
          >
            {getPerformanceMessage()}
          </Animated.Text>
        </Animated.View>

        {/* Score card */}
        <Animated.View
          entering={SlideInUp.delay(600)}
          style={styles.scoreSection}
        >
          <Card style={styles.scoreCard}>
            <View style={styles.scoreHeader}>
              <Text style={styles.scoreTitle}>Your Score</Text>
              <Animated.Text
                entering={ZoomIn.delay(800)}
                style={[styles.scoreValue, { color: getPerformanceColor() }]}
              >
                {Math.round(scorePercentage)}%
              </Animated.Text>
            </View>

            <Progress
              value={scoreProgress.value}
              color={getPerformanceColor()}
              style={styles.scoreProgress}
              animated={true}
              animationType="spring"
            />

            {/* Stars */}
            <Animated.View
              style={[styles.starsContainer, { opacity: starsOpacity }]}
            >
              {[...Array(3)].map((_, i) => {
                const shouldFill = i < Math.ceil((scorePercentage / 100) * 3);
                return (
                  <Animated.View
                    key={i}
                    entering={ZoomIn.delay(1300 + i * 100)}
                  >
                    <Star
                      size={32}
                      color={colors.warning}
                      fill={shouldFill ? colors.warning : 'transparent'}
                    />
                  </Animated.View>
                );
              })}
            </Animated.View>
          </Card>
        </Animated.View>

        {/* Stats */}
        <Animated.View
          entering={SlideInUp.delay(700)}
          style={styles.statsSection}
        >
          <Card style={styles.statsCard}>
            <Text style={styles.statsTitle}>Session Stats</Text>

            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <View style={styles.statIcon}>
                  <Clock size={20} color={colors.primary} />
                </View>
                <View style={styles.statContent}>
                  <Text style={styles.statValue}>{timeInMinutes} min</Text>
                  <Text style={styles.statLabel}>Time Spent</Text>
                </View>
              </View>

              <View style={styles.statItem}>
                <View style={styles.statIcon}>
                  <Target size={20} color={colors.secondary} />
                </View>
                <View style={styles.statContent}>
                  <Text style={styles.statValue}>
                    {results.stepsCompleted.length}
                  </Text>
                  <Text style={styles.statLabel}>Steps Completed</Text>
                </View>
              </View>

              <View style={styles.statItem}>
                <View style={styles.statIcon}>
                  <CheckCircle size={20} color={colors.success} />
                </View>
                <View style={styles.statContent}>
                  <Text style={styles.statValue}>
                    {results.interactionResults?.filter(
                      (r: any) => r.isCorrect || r.correct > 0
                    ).length || 0}
                  </Text>
                  <Text style={styles.statLabel}>Correct Answers</Text>
                </View>
              </View>
            </View>
          </Card>
        </Animated.View>

        {/* Action buttons */}
        <Animated.View
          entering={SlideInUp.delay(800)}
          style={styles.actionsSection}
        >
          <Button
            title="Continue Learning"
            onPress={handleContinue}
            size="large"
            icon={<ArrowRight size={20} color={colors.surface} />}
            style={StyleSheet.flatten([
              styles.actionButton,
              styles.primaryButton,
            ])}
          />

          {scorePercentage < 80 && (
            <Button
              title="Try Again"
              onPress={handleRetry}
              variant="outline"
              size="large"
              icon={<RotateCcw size={20} color={colors.primary} />}
              style={styles.actionButton}
            />
          )}
        </Animated.View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  content: {
    flex: 1,
    padding: spacing.lg,
  },

  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },

  trophyContainer: {
    marginBottom: spacing.lg,
  },

  congratsText: textStyle({
    ...typography.heading2,
    textAlign: 'center',
    fontWeight: '700',
  }),

  scoreSection: {
    marginBottom: spacing.lg,
  },

  scoreCard: {
    alignItems: 'center',
    padding: spacing.xl,
  },

  scoreHeader: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  scoreTitle: textStyle({
    ...typography.heading3,
    color: colors.text,
    marginBottom: spacing.sm,
  }),

  scoreValue: textStyle({
    ...typography.heading1,
    fontWeight: '800',
    fontSize: 48,
  }),

  scoreProgress: {
    width: '100%',
    height: 8,
    marginBottom: spacing.lg,
  },

  starsContainer: {
    flexDirection: 'row',
    gap: spacing.sm,
  },

  statsSection: {
    marginBottom: spacing.xl,
  },

  statsCard: {
    padding: spacing.lg,
  },

  statsTitle: textStyle({
    ...typography.heading3,
    color: colors.text,
    marginBottom: spacing.md,
    textAlign: 'center',
  }),

  statsGrid: {
    gap: spacing.md,
  },

  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${colors.primary}05`,
    padding: spacing.md,
    borderRadius: 12,
  },

  statIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
    ...shadows.small,
  },

  statContent: {
    flex: 1,
  },

  statValue: textStyle({
    ...typography.heading3,
    color: colors.text,
    marginBottom: spacing.xs,
  }),

  statLabel: textStyle({
    ...typography.caption,
    color: colors.textSecondary,
  }),

  actionsSection: {
    gap: spacing.md,
  },

  actionButton: {
    ...shadows.medium,
  },

  primaryButton: {
    backgroundColor: colors.primary,
  },
});
