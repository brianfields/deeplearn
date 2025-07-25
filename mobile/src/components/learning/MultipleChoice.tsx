/**
 * MultipleChoice Component - Interactive Knowledge Assessment
 *
 * This component handles multiple-choice questions that test user understanding
 * after they've consumed educational content. It provides immediate feedback
 * and detailed explanations to reinforce learning.
 *
 * LEARNING FLOW ROLE:
 * - Follows didactic content to assess comprehension
 * - Provides interactive testing of learned concepts
 * - Offers immediate feedback and explanations
 * - Contributes to overall learning session scoring
 *
 * ASSESSMENT FEATURES:
 * - Single-select multiple choice questions
 * - Immediate visual feedback on selection
 * - Automatic progression for correct answers
 * - Manual continuation for incorrect answers (encourages reflection)
 * - Detailed explanations for all answer choices
 *
 * USER EXPERIENCE DESIGN:
 * - Touch-optimized choice selection
 * - Visual feedback with colors and animations
 * - Haptic feedback for selection and results
 * - Clear result indicators (checkmarks, X marks)
 * - Progressive disclosure of explanations
 *
 * MOBILE INTERACTIONS:
 * - Touch-to-select with immediate visual feedback
 * - Animated transitions between states
 * - Haptic feedback for engagement
 * - Auto-submit after selection for streamlined flow
 * - Responsive layout for various screen sizes
 *
 * INTEGRATION WITH LEARNING FLOW:
 * - Receives MCQ data with questions, choices, and correct answers
 * - Returns detailed results including correctness and user selections
 * - Contributes to session-wide scoring and completion tracking
 * - Provides analytics data for learning effectiveness
 *
 * DATA STRUCTURE:
 * - question: The question text
 * - choices: Object mapping choice keys to choice text
 * - correct_answer_index: Index of the correct choice
 * - justifications: Explanations for each choice option
 * - number: Question identifier for tracking
 *
 * RESULT TRACKING:
 * - Records user's selected choice
 * - Tracks correctness for scoring
 * - Captures time spent on question
 * - Stores explanation viewed for analytics
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Vibration,
  Platform,
} from 'react-native';
import Animated, {
  FadeIn,
  SlideInUp,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  ZoomIn,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

// Icons
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react-native';

// Components
import { Button } from '@/components/ui/Button';

// Theme & Types
import { colors, spacing } from '@/utils/theme';
import type { MultipleChoiceProps } from '@/types';

interface ChoiceItemProps {
  letter: string;
  text: string;
  isSelected: boolean;
  isCorrect?: boolean;
  isIncorrect?: boolean;
  onPress: () => void;
  disabled?: boolean;
}

const ChoiceItem: React.FC<ChoiceItemProps> = ({
  letter,
  text,
  isSelected,
  isCorrect,
  isIncorrect,
  onPress,
  disabled = false,
}) => {
  const scaleValue = useSharedValue(1);
  const colorValue = useSharedValue(0);

  useEffect(() => {
    if (isSelected) {
      scaleValue.value = withSpring(0.98, { damping: 15 });
    } else {
      scaleValue.value = withSpring(1);
    }

    if (isCorrect) {
      colorValue.value = withTiming(1);
    } else if (isIncorrect) {
      colorValue.value = withTiming(-1);
    } else {
      colorValue.value = withTiming(0);
    }
  }, [isSelected, isCorrect, isIncorrect]); // eslint-disable-line react-hooks/exhaustive-deps

  const animatedStyle = useAnimatedStyle(() => {
    let backgroundColor = colors.surface;
    let borderColor = colors.border;

    if (colorValue.value === 1) {
      backgroundColor = `${colors.success}20`;
      borderColor = colors.success;
    } else if (colorValue.value === -1) {
      backgroundColor = `${colors.error}20`;
      borderColor = colors.error;
    } else if (isSelected) {
      backgroundColor = `${colors.primary}10`;
      borderColor = colors.primary;
    }

    return {
      transform: [{ scale: scaleValue.value }],
      backgroundColor,
      borderColor,
    };
  });

  const letterStyle = useAnimatedStyle(() => {
    let backgroundColor = colors.border;
    let color = colors.text;

    if (colorValue.value === 1) {
      backgroundColor = colors.success;
      color = colors.surface;
    } else if (colorValue.value === -1) {
      backgroundColor = colors.error;
      color = colors.surface;
    } else if (isSelected) {
      backgroundColor = colors.primary;
      color = colors.surface;
    }

    return {
      backgroundColor,
      color,
    };
  });

  const handlePress = () => {
    if (!disabled) {
      // Haptic feedback
      if (Platform.OS === 'ios') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } else {
        Vibration.vibrate(10);
      }
      onPress();
    }
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      disabled={disabled}
      activeOpacity={0.8}
    >
      <Animated.View style={[styles.choiceItem, animatedStyle]}>
        <Animated.View style={[styles.choiceLetter, letterStyle]}>
          <Text style={[styles.choiceLetterText, { color: letterStyle.color }]}>
            {letter}
          </Text>
        </Animated.View>

        <Text style={styles.choiceText}>{text}</Text>

        {/* Result icon */}
        {isCorrect && (
          <Animated.View entering={ZoomIn} style={styles.resultIcon}>
            <CheckCircle size={24} color={colors.success} />
          </Animated.View>
        )}

        {isIncorrect && (
          <Animated.View entering={ZoomIn} style={styles.resultIcon}>
            <XCircle size={24} color={colors.error} />
          </Animated.View>
        )}
      </Animated.View>
    </TouchableOpacity>
  );
};

export default function MultipleChoice({
  question,
  onComplete,
  isLoading = false,
}: MultipleChoiceProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);

  // Convert choices object to array for easier index-based access
  const choicesArray = Object.entries(question.choices);

  // Generate letter for display (A, B, C, D, etc.)
  const getChoiceLetter = (index: number) => String.fromCharCode(65 + index); // 65 is 'A'

  // Reset state when question changes
  useEffect(() => {
    setSelectedAnswer(null);
    setShowResult(false);
  }, [question]);

  const handleAnswerSelect = (answerIndex: number) => {
    if (showResult || isLoading) return;

    setSelectedAnswer(answerIndex);

    // Auto-submit the answer
    setTimeout(() => {
      handleSubmit(answerIndex);
    }, 300); // Small delay for visual feedback
  };

  const handleSubmit = (answerIndex: number) => {
    if (question.correct_answer_index === undefined) return;

    const isCorrect = answerIndex === question.correct_answer_index;
    const selectedChoice = choicesArray[answerIndex];
    const selectedLetter = getChoiceLetter(answerIndex);

    const result = {
      questionId: question.number?.toString() || '0',
      question: question.question,
      selectedOption: selectedLetter, // For backward compatibility with results
      selectedText: selectedChoice[1], // The choice text
      isCorrect,
      explanation: question.justifications[selectedChoice[0]] || '', // Use original letter key for justifications
    };

    setShowResult(true);

    // Haptic feedback for result
    if (Platform.OS === 'ios') {
      Haptics.impactAsync(
        isCorrect
          ? Haptics.ImpactFeedbackStyle.Medium
          : Haptics.ImpactFeedbackStyle.Heavy
      );
    } else {
      Vibration.vibrate(isCorrect ? 50 : [0, 100, 50, 100]);
    }

    // Handle completion based on correctness
    if (isCorrect) {
      // Auto-proceed for correct answers after showing result
      setTimeout(() => {
        onComplete({
          componentType: 'multiple_choice_question',
          timeSpent: 0,
          completed: true,
          data: {
            correct: 1,
            total: 1,
            details: [result],
          },
        });
      }, 1500); // Show correct feedback briefly then auto-proceed
    }
    // For incorrect answers, user must press Continue button
  };

  const handleContinue = () => {
    if (selectedAnswer === null) return;

    const selectedChoice = choicesArray[selectedAnswer];
    const selectedLetter = getChoiceLetter(selectedAnswer);

    const result = {
      questionId: question.number?.toString() || '0',
      question: question.question,
      selectedOption: selectedLetter,
      selectedText: selectedChoice[1],
      isCorrect: false,
      explanation: question.justifications[selectedChoice[0]] || '',
    };

    onComplete({
      componentType: 'multiple_choice_question',
      timeSpent: 0,
      completed: true,
      data: {
        correct: 0,
        total: 1,
        details: [result],
      },
    });
  };

  if (!question) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>No question available</Text>
        </View>
      </View>
    );
  }

  const isCorrectAnswer = selectedAnswer === question.correct_answer_index;
  const isIncorrectAnswer =
    showResult && selectedAnswer !== null && !isCorrectAnswer;

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Question */}
        <Animated.View
          key={question.number || 'question'}
          entering={SlideInUp}
          style={styles.content}
        >
          <View style={styles.questionSection}>
            <Text style={styles.questionText}>{question.question}</Text>
          </View>

          {/* Choices */}
          <View style={styles.choicesContainer}>
            {choicesArray.map(([_letter, text], index) => (
              <Animated.View
                key={index}
                entering={FadeIn.delay(200 + index * 100)}
                style={styles.choiceWrapper}
              >
                <ChoiceItem
                  letter={getChoiceLetter(index)}
                  text={text}
                  isSelected={selectedAnswer === index}
                  isCorrect={
                    showResult && index === question.correct_answer_index
                  }
                  isIncorrect={
                    showResult &&
                    selectedAnswer === index &&
                    index !== question.correct_answer_index
                  }
                  onPress={() => handleAnswerSelect(index)}
                  disabled={showResult || isLoading}
                />
              </Animated.View>
            ))}
          </View>

          {/* Explanation */}
          {showResult &&
            selectedAnswer !== null &&
            question.justifications[choicesArray[selectedAnswer]![0]] && (
              <Animated.View
                entering={SlideInUp.delay(300)}
                style={styles.explanationContainer}
              >
                <View style={styles.explanationCard}>
                  <View style={styles.explanationHeader}>
                    <Text style={styles.explanationTitle}>
                      {isCorrectAnswer ? 'Correct!' : 'Explanation'}
                    </Text>
                  </View>
                  <Text style={styles.explanationText}>
                    {question.justifications[choicesArray[selectedAnswer]![0]]}
                  </Text>
                </View>
              </Animated.View>
            )}
        </Animated.View>
      </ScrollView>

      {/* Action buttons - only show Continue for incorrect answers */}
      {isIncorrectAnswer && (
        <Animated.View
          entering={SlideInUp.delay(400)}
          style={styles.actionContainer}
        >
          <Button
            title="Continue"
            onPress={handleContinue}
            size="large"
            icon={<ArrowRight size={20} color={colors.surface} />}
            style={styles.actionButton}
          />
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },

  errorText: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 24,
    color: colors.textSecondary,
    textAlign: 'center',
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    paddingBottom: spacing.xxl,
  },

  content: {
    flex: 1,
    padding: spacing.lg,
  },

  questionSection: {
    marginBottom: spacing.xl,
  },

  questionText: {
    fontSize: 20,
    fontWeight: '600' as const,
    lineHeight: 30,
    color: colors.text,
    letterSpacing: -0.32,
  },

  choicesContainer: {
    gap: spacing.md,
    marginBottom: spacing.lg,
  },

  choiceWrapper: {
    // Wrapper for animation
  },

  choiceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },

  choiceLetter: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
    backgroundColor: colors.border,
  },

  choiceLetterText: {
    fontSize: 14,
    fontWeight: '600' as const,
    color: colors.text,
  },

  choiceText: {
    fontSize: 17,
    fontWeight: '400' as const,
    color: colors.text,
    flex: 1,
    lineHeight: 24,
    letterSpacing: -0.24,
  },

  resultIcon: {
    marginLeft: spacing.sm,
  },

  explanationContainer: {
    marginBottom: spacing.lg,
  },

  explanationCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },

  explanationHeader: {
    marginBottom: spacing.sm,
  },

  explanationTitle: {
    fontSize: 18,
    fontWeight: '600' as const,
    color: colors.text,
    letterSpacing: -0.32,
  },

  explanationText: {
    fontSize: 17,
    fontWeight: '400' as const,
    lineHeight: 26,
    color: colors.text,
    letterSpacing: -0.24,
  },

  actionContainer: {
    padding: spacing.lg,
    paddingTop: 0,
  },

  actionButton: {
    // Clean button styling
  },
});
