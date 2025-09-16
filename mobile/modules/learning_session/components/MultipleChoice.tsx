/**
 * MultipleChoice Component - Interactive Knowledge Assessment
 *
 * This component handles multiple-choice questions that test user understanding
 * after they've consumed educational content. It provides immediate feedback
 * and detailed explanations to reinforce learning.
 *
 * Based on the original MultipleChoice component, adapted for the new modular architecture.
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
import { CheckCircle, XCircle } from 'lucide-react-native';

// Components
import { Button } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';

// Support both old and new MCQ formats
interface MCQOption {
  label: string;
  text: string;
  rationale_wrong?: string;
}

interface MultipleChoiceQuestion {
  question: string;
  options: string[] | MCQOption[]; // Support both formats
  correct_answer: number; // index
  explanation?: string;
  number?: number;
}

interface MultipleChoiceProps {
  question: MultipleChoiceQuestion;
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

interface ChoiceItemProps {
  letter: string;
  text: string;
  isSelected: boolean;
  isCorrect?: boolean;
  isIncorrect?: boolean;
  onPress: () => void;
  disabled?: boolean;
  testID?: string;
}

const ChoiceItem: React.FC<ChoiceItemProps> = ({
  letter,
  text,
  isSelected,
  isCorrect,
  isIncorrect,
  onPress,
  disabled = false,
  testID,
}) => {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();

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
    let backgroundColor = theme.colors?.surface || '#FFFFFF';
    let borderColor = theme.colors?.border || '#E5E5E7';

    if (colorValue.value === 1) {
      backgroundColor = `${theme.colors?.success || '#34C759'}20`;
      borderColor = theme.colors?.success || '#34C759';
    } else if (colorValue.value === -1) {
      backgroundColor = `${theme.colors?.error || '#FF3B30'}20`;
      borderColor = theme.colors?.error || '#FF3B30';
    } else if (isSelected) {
      backgroundColor = `${theme.colors?.primary || '#007AFF'}10`;
      borderColor = theme.colors?.primary || '#007AFF';
    }

    return {
      transform: [{ scale: scaleValue.value }],
      backgroundColor,
      borderColor,
    };
  });

  const letterStyle = useAnimatedStyle(() => {
    let backgroundColor = theme.colors?.border || '#E5E5E7';
    let color = theme.colors?.text || '#000000';

    if (colorValue.value === 1) {
      backgroundColor = theme.colors?.success || '#34C759';
      color = theme.colors?.surface || '#FFFFFF';
    } else if (colorValue.value === -1) {
      backgroundColor = theme.colors?.error || '#FF3B30';
      color = theme.colors?.surface || '#FFFFFF';
    } else if (isSelected) {
      backgroundColor = theme.colors?.primary || '#007AFF';
      color = theme.colors?.surface || '#FFFFFF';
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

  const styles = StyleSheet.create({
    choiceItem: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 16,
      paddingHorizontal: 12,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: theme.colors?.border || '#E5E5E7',
      backgroundColor: theme.colors?.surface || '#FFFFFF',
    },
    choiceLetter: {
      width: 28,
      height: 28,
      borderRadius: 14,
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
      backgroundColor: theme.colors?.border || '#E5E5E7',
    },
    choiceLetterText: {
      fontSize: 14,
      fontWeight: '600' as const,
      color: theme.colors?.text || '#000000',
    },
    choiceText: {
      fontSize: 17,
      fontWeight: '400' as const,
      color: theme.colors?.text || '#000000',
      flex: 1,
      lineHeight: 24,
      letterSpacing: -0.24,
    },
    resultIcon: {
      marginLeft: 12,
    },
  });

  return (
    <TouchableOpacity
      onPress={handlePress}
      disabled={disabled}
      activeOpacity={0.8}
      testID={testID}
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
            <CheckCircle size={24} color={theme.colors?.success || '#34C759'} />
          </Animated.View>
        )}

        {isIncorrect && (
          <Animated.View entering={ZoomIn} style={styles.resultIcon}>
            <XCircle size={24} color={theme.colors?.error || '#FF3B30'} />
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
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);

  // Build choices as letter -> text from options array
  // Handle both old format (string[]) and new format (MCQOption[])
  const choicesArray: Array<[string, string]> = (question.options || []).map(
    (option, idx) => {
      if (typeof option === 'string') {
        // Old format: options are strings
        return [String.fromCharCode(65 + idx), option] as [string, string];
      } else {
        // New format: options are objects with {label, text, rationale_wrong}
        return [option.label || String.fromCharCode(65 + idx), option.text] as [
          string,
          string,
        ];
      }
    }
  );

  // Find the correct answer index by matching the label
  const correctIndex = choicesArray.findIndex(
    ([label, _]) => label === question.correct_answer.toString()
  );

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
    if (correctIndex === undefined) return;

    const isCorrect = answerIndex === correctIndex;

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
      explanation: question.explanation || '',
    };

    onComplete({
      componentType: 'multiple_choice_question',
      timeSpent: 0,
      completed: true,
      isCorrect: false,
      userAnswer: selectedLetter,
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

  const isCorrectAnswer = selectedAnswer === correctIndex;

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
                  isCorrect={showResult && index === correctIndex}
                  isIncorrect={
                    showResult &&
                    selectedAnswer === index &&
                    index !== correctIndex
                  }
                  onPress={() => handleAnswerSelect(index)}
                  disabled={showResult || isLoading}
                  testID={`mcq-choice-${index}`}
                />
              </Animated.View>
            ))}
          </View>

          {/* Explanation */}
          {showResult && selectedAnswer !== null && question.explanation && (
            <Animated.View
              entering={SlideInUp.delay(300)}
              style={styles.explanationContainer}
              testID="mcq-explanation"
            >
              <View style={styles.explanationCard}>
                <View style={styles.explanationHeader}>
                  <Text style={styles.explanationTitle}>
                    {isCorrectAnswer ? 'Correct!' : 'Explanation'}
                  </Text>
                </View>
                <Text style={styles.explanationText}>
                  {question.explanation}
                </Text>
              </View>
            </Animated.View>
          )}
        </Animated.View>
      </ScrollView>

      {/* Action buttons - only show Continue for incorrect answers */}
      {selectedAnswer !== null && (
        <Animated.View
          entering={SlideInUp.delay(400)}
          style={styles.actionContainer}
        >
          <Button
            title="Continue"
            onPress={handleContinue}
            size="large"
            style={styles.actionButton}
            testID="mcq-continue-button"
          />
        </Animated.View>
      )}
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },

    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
    },

    errorText: {
      fontSize: 16,
      fontWeight: '400' as const,
      lineHeight: 24,
      color: theme.colors?.textSecondary || '#666666',
      textAlign: 'center',
    },

    scrollView: {
      flex: 1,
    },

    scrollContent: {
      paddingBottom: 40,
    },

    content: {
      flex: 1,
      padding: 20,
    },

    questionSection: {
      marginBottom: 24,
    },

    questionText: {
      fontSize: 20,
      fontWeight: '600' as const,
      lineHeight: 30,
      color: theme.colors?.text || '#000000',
      letterSpacing: -0.32,
    },

    choicesContainer: {
      gap: 16,
      marginBottom: 20,
    },

    choiceWrapper: {
      // Wrapper for animation
    },

    explanationContainer: {
      marginBottom: 20,
    },

    explanationCard: {
      backgroundColor: theme.colors?.surface || '#FFFFFF',
      borderRadius: 16,
      padding: 20,
      borderWidth: 1,
      borderColor: theme.colors?.border || '#E5E5E7',
    },

    explanationHeader: {
      marginBottom: 12,
    },

    explanationTitle: {
      fontSize: 18,
      fontWeight: '600' as const,
      color: theme.colors?.text || '#000000',
      letterSpacing: -0.32,
    },

    explanationText: {
      fontSize: 17,
      fontWeight: '400' as const,
      lineHeight: 26,
      color: theme.colors?.text || '#000000',
      letterSpacing: -0.24,
    },

    actionContainer: {
      padding: 20,
      paddingTop: 0,
    },

    actionButton: {
      // Clean button styling
    },
  });
