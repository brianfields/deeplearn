/**
 * Duolingo Learning Flow for React Native
 *
 * Adapted from the web version with mobile-specific optimizations:
 * - Native animations
 * - Touch interactions
 * - Mobile navigation
 * - Performance optimizations
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  BackHandler,
  Alert,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  withTiming,
  withSpring,
  useSharedValue,
  FadeIn,
  SlideInRight,
  SlideOutLeft,
} from 'react-native-reanimated';
import { useFocusEffect } from '@react-navigation/native';

// Icons (using Lucide React Native)
import {
  ArrowLeft,
  Trophy,
  Flame,
  Target,
  Star,
  AlertCircle,
} from 'lucide-react-native';

// Components
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import DidacticSnippet from './DidacticSnippet';
import MultipleChoice from './MultipleChoice';

// Services & Types
import { learningService } from '@/services/learning-service';
import {
  colors,
  spacing,
  typography,
  shadows,
  responsive,
} from '@/utils/theme';
import type {
  BiteSizedTopicDetail,
  ComponentType,
  LearningResults,
  MultipleChoiceQuestion,
} from '@/types';

interface DuolingoLearningFlowProps {
  topic: BiteSizedTopicDetail;
  onComplete: (results: LearningResults) => void;
  onBack: () => void;
}

interface ComponentStep {
  type: ComponentType;
  components: any[];
  currentIndex: number;
  isCompleted: boolean;
}

export default function DuolingoLearningFlow({
  topic,
  onComplete,
  onBack,
}: DuolingoLearningFlowProps) {
  console.log(
    '🎯 [Mobile Learning Flow] Component mounted with topic:',
    topic?.title
  );

  // State
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [startTime] = useState(Date.now());
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [interactionResults, setInteractionResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streakCount, setStreakCount] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);

  // Animated values
  const celebrationScale = useSharedValue(0);
  const progressValue = useSharedValue(0);

  // Organize components into individual steps
  const componentSteps = useMemo((): ComponentStep[] => {
    console.log(
      '🔧 [Mobile Learning Flow] Organizing components:',
      topic.components
    );
    const steps: ComponentStep[] = [];

    // Add didactic snippet first (if available)
    const didacticComponents = topic.components.filter(
      c => c.component_type === 'didactic_snippet'
    );
    if (didacticComponents.length > 0) {
      steps.push({
        type: 'didactic_snippet',
        components: didacticComponents,
        currentIndex: 0,
        isCompleted: false,
      });
    }

    // Add each MCQ as an individual step
    const mcqComponents = topic.components.filter(
      c => c.component_type === 'mcq'
    );
    mcqComponents.forEach(mcqComponent => {
      steps.push({
        type: 'mcq',
        components: [mcqComponent], // Single MCQ per step
        currentIndex: 0,
        isCompleted: false,
      });
    });

    return steps;
  }, [topic.components]);

  const currentStep = componentSteps[currentStepIndex];
  const totalSteps = componentSteps.length;
  const progress = totalSteps > 0 ? (currentStepIndex / totalSteps) * 100 : 0;

  // Handle Android back button
  useFocusEffect(
    useCallback(() => {
      const onBackPress = () => {
        Alert.alert(
          'Leave Learning Session?',
          'Your progress will be saved, but you will need to restart this topic.',
          [
            { text: 'Stay', style: 'cancel' },
            { text: 'Leave', style: 'destructive', onPress: onBack },
          ]
        );
        return true;
      };

      const subscription = BackHandler.addEventListener(
        'hardwareBackPress',
        onBackPress
      );
      return () => subscription.remove();
    }, [onBack])
  );

  // Load streak count on mount
  useEffect(() => {
    const stats = learningService.getCacheStats();
    setStreakCount(stats.currentStreak);
  }, []);

  // Save progress continuously
  useEffect(() => {
    learningService.saveTopicProgress(topic.id, {
      currentComponentIndex: currentStepIndex,
      completedComponents: completedSteps,
      timeSpent: Date.now() - startTime,
      interactionResults,
    });
  }, [
    topic.id,
    currentStepIndex,
    completedSteps,
    startTime,
    interactionResults,
  ]);

  // Update progress animation
  useEffect(() => {
    progressValue.value = withSpring(progress);
  }, [progress]); // eslint-disable-line react-hooks/exhaustive-deps

  // Celebration animation
  useEffect(() => {
    if (showCelebration) {
      celebrationScale.value = withSpring(1, {
        damping: 10,
        stiffness: 100,
      });
    } else {
      celebrationScale.value = withTiming(0, { duration: 200 });
    }
  }, [showCelebration]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStepComplete = useCallback(
    (stepType: string, results?: any) => {
      setCompletedSteps(prev => [...prev, stepType]);

      if (results) {
        setInteractionResults(prev => [...prev, results]);
      }

      // Move to next step or complete
      if (currentStepIndex < componentSteps.length - 1) {
        setCurrentStepIndex(prev => prev + 1);

        // Show mini celebration for good progress
        if (
          results?.correct !== undefined &&
          results.correct / results.total >= 0.8
        ) {
          setShowCelebration(true);
          setTimeout(() => setShowCelebration(false), 1500);
        }
      } else {
        handleTopicComplete();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentStepIndex, componentSteps.length]
  );

  const handleTopicComplete = useCallback(async () => {
    setIsLoading(true);

    try {
      const timeSpent = Math.round((Date.now() - startTime) / 1000);

      // Calculate final score
      let finalScore = 100;
      if (interactionResults.length > 0) {
        const scores = interactionResults.map(result => {
          if (result.correct !== undefined) {
            return (result.correct / result.total) * 100;
          }
          return result.score || 80;
        });
        finalScore = Math.round(
          scores.reduce((sum, score) => sum + score, 0) / scores.length
        );
      }

      const learningResults: LearningResults = {
        topicId: topic.id,
        timeSpent,
        stepsCompleted: completedSteps,
        interactionResults,
        finalScore,
        completed: true,
      };

      // Submit results to learning service
      await learningService.submitTopicResults(topic.id, learningResults);

      setIsLoading(false);

      // Show celebration
      setShowCelebration(true);

      // Complete after animation
      setTimeout(() => {
        onComplete(learningResults);
      }, 2000);
    } catch (error) {
      console.error('Failed to submit topic results:', error);
      setIsLoading(false);
      // Could show error toast here or retry logic
    }
  }, [startTime, completedSteps, interactionResults, topic.id, onComplete]);

  const renderCurrentComponent = () => {
    if (!currentStep) {
      return (
        <View style={styles.errorContainer}>
          <AlertCircle size={64} color={colors.error} />
          <Text style={styles.errorText}>No learning steps available</Text>
        </View>
      );
    }

    const currentComponent = currentStep.components[currentStep.currentIndex];

    switch (currentStep.type) {
      case 'didactic_snippet':
        return (
          <DidacticSnippet
            snippet={currentComponent.content}
            onContinue={() => handleStepComplete('didactic')}
            isLoading={isLoading}
          />
        );

      case 'mcq': {
        // MCQ data is now in correct MultipleChoiceQuestion format from backend
        const mcqQuestion = currentComponent.content as MultipleChoiceQuestion;

        // Validate that we have the expected structure
        if (
          !mcqQuestion.choices ||
          Object.keys(mcqQuestion.choices).length === 0
        ) {
          return (
            <View style={styles.errorContainer}>
              <AlertCircle size={64} color={colors.error} />
              <Text style={styles.errorText}>Content Error</Text>
              <Text style={styles.errorSubtext}>
                This question doesn&apos;t have valid options to display.
              </Text>
              <Button
                title="Skip Question"
                onPress={() =>
                  handleStepComplete('mcq', { correct: 0, total: 1 })
                }
                style={styles.skipButton}
              />
            </View>
          );
        }

        return (
          <MultipleChoice
            question={mcqQuestion}
            onComplete={(results: any) => handleStepComplete('mcq', results)}
            isLoading={isLoading}
          />
        );
      }

      default:
        return null;
    }
  };

  const celebrationStyle = useAnimatedStyle(() => ({
    transform: [{ scale: celebrationScale.value }],
    opacity: celebrationScale.value,
  }));

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Header with progress */}
      <View style={styles.header}>
        <Button
          title=""
          onPress={onBack}
          variant="ghost"
          size="small"
          icon={<ArrowLeft size={20} color={colors.text} />}
          style={styles.backButton}
        />

        <View style={styles.progressContainer}>
          <View style={styles.progressInfo}>
            <View style={styles.streakContainer}>
              <Flame size={16} color={colors.accent} />
              <Text style={styles.streakText}>{streakCount}</Text>
            </View>
            <Text style={styles.stepText}>
              Step {currentStepIndex + 1} of {totalSteps}
            </Text>
          </View>
          <Progress value={progress} style={styles.progressBar} />
        </View>

        <View style={styles.badgeContainer}>
          <Target size={12} color={colors.secondary} />
          <Text style={styles.badgeText}>{Math.round(progress)}%</Text>
        </View>
      </View>

      {/* Main content */}
      <View style={styles.content}>
        {currentStep && (
          <Animated.View
            key={`${currentStep.type}-${currentStepIndex}`}
            entering={SlideInRight}
            exiting={SlideOutLeft}
            style={styles.componentContainer}
          >
            {renderCurrentComponent()}
          </Animated.View>
        )}
      </View>

      {/* Celebration overlay */}
      {showCelebration && (
        <Animated.View style={[styles.celebrationOverlay, celebrationStyle]}>
          <Card style={styles.celebrationCard}>
            <Animated.View entering={FadeIn.delay(200)}>
              <Trophy size={64} color={colors.warning} />
            </Animated.View>
            <Text style={styles.celebrationTitle}>Great job!</Text>
            <Text style={styles.celebrationText}>
              {currentStepIndex === componentSteps.length - 1
                ? `You completed "${topic.title}"!`
                : 'Keep it up!'}
            </Text>
            <View style={styles.starsContainer}>
              {[...Array(5)].map((_, i) => (
                <Animated.View key={i} entering={FadeIn.delay(300 + i * 100)}>
                  <Star
                    size={20}
                    color={colors.warning}
                    fill={colors.warning}
                  />
                </Animated.View>
              ))}
            </View>
          </Card>
        </Animated.View>
      )}

      {/* Mini progress indicator for steps */}
      <View style={styles.stepIndicator}>
        <Card style={styles.stepIndicatorCard} padding="sm">
          <View style={styles.dotsContainer}>
            {componentSteps.map((step, index) => (
              <View
                key={step.type}
                style={[
                  styles.dot,
                  index < currentStepIndex && styles.dotCompleted,
                  index === currentStepIndex && styles.dotCurrent,
                ]}
              />
            ))}
          </View>
        </Card>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    ...shadows.small,
  },

  backButton: {
    width: 40,
    height: 40,
  },

  progressContainer: {
    flex: 1,
    marginHorizontal: spacing.md,
  },

  progressInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },

  streakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  streakText: {
    ...typography.caption,
    fontWeight: '600',
    color: colors.accent,
    marginLeft: spacing.xs,
  },

  stepText: {
    fontSize: 12,
    fontWeight: '400' as const,
    lineHeight: 16,
    color: colors.textSecondary,
  },

  progressBar: {
    height: 6,
  },

  badgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.secondary,
  },

  badgeText: {
    ...typography.caption,
    fontWeight: '600',
    color: colors.secondary,
    marginLeft: spacing.xs,
  },

  content: {
    flex: 1,
    padding: spacing.md,
  },

  componentContainer: {
    flex: 1,
  },

  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },

  errorText: {
    ...(typography.heading3 as any),
    color: colors.error,
    marginTop: spacing.md,
    textAlign: 'center',
  },

  errorSubtext: {
    ...(typography.body as any),
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },

  skipButton: {
    marginTop: spacing.lg,
  },

  celebrationOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },

  celebrationCard: {
    alignItems: 'center',
    maxWidth: responsive.wp(80),
    margin: spacing.md,
  },

  celebrationTitle: {
    ...(typography.heading2 as any),
    color: colors.text,
    marginTop: spacing.md,
    textAlign: 'center',
  },

  celebrationText: {
    ...(typography.body as any),
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },

  starsContainer: {
    flexDirection: 'row',
    marginTop: spacing.md,
    gap: spacing.xs,
  },

  stepIndicator: {
    position: 'absolute',
    bottom: spacing.lg,
    left: 0,
    right: 0,
    alignItems: 'center',
  },

  stepIndicatorCard: {
    backgroundColor: `${colors.surface}E6`, // Semi-transparent
  },

  dotsContainer: {
    flexDirection: 'row',
    gap: spacing.xs,
  },

  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.border,
  },

  dotCompleted: {
    backgroundColor: colors.secondary,
  },

  dotCurrent: {
    backgroundColor: colors.primary,
    transform: [{ scale: 1.25 }],
  },
});
