/**
 * ShortAnswer Component - Free Response Assessment
 *
 * Provides a mobile-friendly interface for answering short-answer exercises
 * with offline fuzzy validation and rich feedback.
 */

import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import Animated, {
  FadeInUp,
  FadeOutDown,
  SlideInUp,
} from 'react-native-reanimated';
import { CheckCircle, XCircle } from 'lucide-react-native';
import { Button, useHaptics, uiSystemProvider } from '../../ui_system/public';
import type { Theme } from '../../ui_system/public';
import type {
  ShortAnswerContentDTO,
  ShortAnswerValidationResult,
} from '../models';
import { validateShortAnswer } from '../service';

interface ShortAnswerProps {
  question: ShortAnswerContentDTO;
  onComplete: (result: {
    componentType: string;
    timeSpent: number;
    completed: boolean;
    isCorrect: boolean;
    userAnswer: string;
    data: Record<string, unknown>;
  }) => void;
  isLoading?: boolean;
}

const MAX_CHAR_COUNT = 50;

const ShortAnswer: React.FC<ShortAnswerProps> = ({
  question,
  onComplete,
  isLoading = false,
}) => {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const { trigger } = useHaptics();

  const [answer, setAnswer] = useState('');
  const [validation, setValidation] =
    useState<ShortAnswerValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const styles = useMemo(() => createStyles(theme), [theme]);

  const handleChange = (value: string) => {
    setAnswer(value.slice(0, MAX_CHAR_COUNT));
  };

  const handleSubmit = async () => {
    if (!answer.trim()) {
      return;
    }
    setIsValidating(true);
    try {
      const result = validateShortAnswer(answer, question);
      setValidation(result);
      setHasSubmitted(true);
      trigger(result.isCorrect ? 'success' : 'medium');
    } finally {
      setIsValidating(false);
    }
  };

  const handleContinue = () => {
    if (!validation) {
      return;
    }

    onComplete({
      componentType: 'short_answer_question',
      timeSpent: 0,
      completed: true,
      isCorrect: validation.isCorrect,
      userAnswer: answer.trim(),
      data: {
        matchedAnswer: validation.matchedAnswer,
        wrongAnswerExplanation: validation.wrongAnswerExplanation,
        canonicalAnswer: question.canonicalAnswer,
        acceptableAnswers: question.acceptableAnswers,
      },
    });
  };

  const showFeedback = hasSubmitted && validation !== null;
  const isSubmitDisabled =
    !answer.trim() || isLoading || isValidating || hasSubmitted;

  return (
    <KeyboardAvoidingView
      behavior={Platform.select({ ios: 'padding', android: undefined })}
      style={styles.container}
    >
      <View style={styles.contentWrapper}>
        <Animated.View
          entering={SlideInUp.springify().damping(18)}
          style={styles.promptContainer}
        >
          <Text style={styles.promptHeading}>Short Answer</Text>
          <Text style={styles.promptText}>{question.question}</Text>
        </Animated.View>

        <View style={styles.inputContainer}>
          <TextInput
            value={answer}
            onChangeText={handleChange}
            placeholder="Type your answer"
            placeholderTextColor={theme.colors.textSecondary}
            style={styles.input}
            autoFocus
            editable={!hasSubmitted && !isLoading && !isValidating}
            maxLength={MAX_CHAR_COUNT}
            testID="short-answer-input"
            returnKeyType="done"
            onSubmitEditing={handleSubmit}
          />
          <Text
            style={styles.charCount}
          >{`${answer.length}/${MAX_CHAR_COUNT}`}</Text>
        </View>

        <Button
          title="Submit"
          onPress={handleSubmit}
          loading={isValidating}
          disabled={isSubmitDisabled}
          testID="short-answer-submit"
          fullWidth
        />

        {showFeedback && validation && (
          <Animated.View
            entering={FadeInUp.springify().damping(20)}
            exiting={FadeOutDown.springify().damping(18)}
            style={styles.feedbackContainer}
            testID="short-answer-feedback"
          >
            <View style={styles.feedbackHeader}>
              {validation.isCorrect ? (
                <CheckCircle size={28} color={theme.colors.success} />
              ) : (
                <XCircle size={28} color={theme.colors.error} />
              )}
              <Text
                style={[
                  styles.feedbackTitle,
                  validation.isCorrect
                    ? styles.feedbackTitleCorrect
                    : styles.feedbackTitleIncorrect,
                ]}
              >
                {validation.isCorrect ? 'Correct!' : 'Not quite'}
              </Text>
            </View>

            <View style={styles.feedbackBody}>
              <Text style={styles.feedbackText}>
                {validation.isCorrect
                  ? question.explanationCorrect
                  : (validation.wrongAnswerExplanation ??
                    question.explanationCorrect)}
              </Text>

              {!validation.isCorrect && (
                <View style={styles.correctAnswersContainer}>
                  <Text style={styles.correctAnswersLabel}>
                    Correct answers
                  </Text>
                  <Text style={styles.correctAnswersText}>
                    {[question.canonicalAnswer, ...question.acceptableAnswers]
                      .filter(Boolean)
                      .join(', ')}
                  </Text>
                </View>
              )}
            </View>

            <Button
              title="Continue"
              onPress={handleContinue}
              variant="secondary"
              fullWidth
              testID="short-answer-continue"
              loading={isLoading}
              disabled={isLoading}
            />
          </Animated.View>
        )}
      </View>
    </KeyboardAvoidingView>
  );
};

function createStyles(theme: Theme) {
  return StyleSheet.create({
    container: {
      flex: 1,
      justifyContent: 'flex-start',
      paddingHorizontal: theme.spacing?.lg ?? 20,
      paddingVertical: theme.spacing?.xl ?? 24,
    },
    contentWrapper: {
      flex: 1,
      gap: theme.spacing?.lg ?? 20,
    },
    promptContainer: {
      gap: theme.spacing?.sm ?? 8,
    },
    promptHeading: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.colors.textSecondary,
      textTransform: 'uppercase',
      letterSpacing: 1,
    },
    promptText: {
      fontSize: 20,
      lineHeight: 28,
      color: theme.colors.text,
      fontWeight: '600',
    },
    inputContainer: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      paddingHorizontal: theme.spacing?.md ?? 16,
      paddingVertical: theme.spacing?.sm ?? 12,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    input: {
      fontSize: 18,
      lineHeight: 24,
      color: theme.colors.text,
      fontWeight: '500',
    },
    charCount: {
      alignSelf: 'flex-end',
      fontSize: 12,
      marginTop: theme.spacing?.xs ?? 4,
      color: theme.colors.textSecondary,
    },
    feedbackContainer: {
      marginTop: theme.spacing?.lg ?? 20,
      gap: theme.spacing?.md ?? 16,
      backgroundColor: `${theme.colors.surface}F2`,
      borderRadius: 16,
      padding: theme.spacing?.lg ?? 20,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    feedbackHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: theme.spacing?.sm ?? 8,
    },
    feedbackTitle: {
      fontSize: 18,
      fontWeight: '700',
    },
    feedbackTitleCorrect: {
      color: theme.colors.success,
    },
    feedbackTitleIncorrect: {
      color: theme.colors.error,
    },
    feedbackBody: {
      gap: theme.spacing?.sm ?? 8,
    },
    feedbackText: {
      fontSize: 16,
      lineHeight: 24,
      color: theme.colors.text,
    },
    correctAnswersContainer: {
      gap: theme.spacing?.xs ?? 4,
      marginTop: theme.spacing?.xs ?? 4,
    },
    correctAnswersLabel: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.colors.textSecondary,
      textTransform: 'uppercase',
      letterSpacing: 0.8,
    },
    correctAnswersText: {
      fontSize: 14,
      color: theme.colors.text,
    },
  });
}

export default ShortAnswer;
