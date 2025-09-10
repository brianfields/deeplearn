/**
 * MultipleChoice Component - Interactive Knowledge Assessment
 *
 * Handles multiple-choice questions that test user understanding
 * after they've consumed educational content.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Vibration,
} from 'react-native';
import { Button, Card } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { CheckCircle, XCircle, Clock, Target } from 'lucide-react-native';
import { useComponentState } from '../store';
import type { ComponentState } from '../models';

interface MultipleChoiceProps {
  component: ComponentState;
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

interface MCQContent {
  stem?: string;
  question?: string;
  options: string[];
  correct_answer?: string;
  correct_answer_index?: number;
  rationale?: string;
  learning_objective?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  max_attempts?: number;
}

export default function MultipleChoice({
  component,
  onComplete,
  isLoading = false,
}: MultipleChoiceProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

  // Component state management
  const { start, timeSpent, state } = useComponentState(component.id);

  // Local state
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [attempts, setAttempts] = useState(state?.attempts || 0);
  const [startTime, setStartTime] = useState<number>(Date.now());

  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const shakeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  // Extract content from component
  const content: MCQContent = component.content || {};
  const {
    stem,
    question,
    options = ['Option A', 'Option B', 'Option C', 'Option D'],
    correct_answer,
    correct_answer_index,
    rationale,
    learning_objective,
    difficulty = 'medium',
    max_attempts = 3,
  } = content;

  // Determine question text and correct answer
  const questionText = stem || question || 'Question will be displayed here.';
  const correctIndex =
    correct_answer_index ??
    (correct_answer ? options.indexOf(correct_answer) : 0);

  // Start tracking when component mounts
  useEffect(() => {
    start();
    setStartTime(Date.now());

    // Animate content in
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();
  }, [start, fadeAnim]);

  // Handle answer selection
  const handleAnswerSelect = (answerIndex: number) => {
    if (showResult || selectedAnswer !== null) return;

    setSelectedAnswer(answerIndex);
    const isCorrect = answerIndex === correctIndex;
    const currentAttempts = attempts + 1;
    setAttempts(currentAttempts);

    // Haptic feedback
    if (isCorrect) {
      // Success vibration pattern
      Vibration.vibrate([100, 50, 100]);
    } else {
      // Error vibration
      Vibration.vibrate(200);

      // Shake animation for incorrect answer
      Animated.sequence([
        Animated.timing(shakeAnim, {
          toValue: 10,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(shakeAnim, {
          toValue: -10,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(shakeAnim, {
          toValue: 0,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start();
    }

    // Show result after a brief delay
    setTimeout(() => {
      setShowResult(true);

      // Scale animation for result
      Animated.spring(scaleAnim, {
        toValue: 1.05,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }).start(() => {
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 100,
          friction: 8,
          useNativeDriver: true,
        }).start();
      });
    }, 500);
  };

  // Handle retry (for incorrect answers)
  const handleRetry = () => {
    if (attempts >= max_attempts) return;

    setSelectedAnswer(null);
    setShowResult(false);
    setShowExplanation(false);
  };

  // Handle continue to next component
  const handleContinue = () => {
    const timeSpentSeconds = (Date.now() - startTime) / 1000;
    const isCorrect = selectedAnswer === correctIndex;

    onComplete({
      componentId: component.id,
      userAnswer: selectedAnswer !== null ? options[selectedAnswer] : null,
      userAnswerIndex: selectedAnswer,
      isCorrect,
      timeSpent: timeSpentSeconds,
      attempts,
      maxAttempts: max_attempts,
    });
  };

  // Show explanation
  const handleShowExplanation = () => {
    setShowExplanation(true);
  };

  // Render option with styling based on state
  const renderOption = (option: string, index: number) => {
    const isSelected = selectedAnswer === index;
    const isCorrect = index === correctIndex;
    const isWrong = showResult && isSelected && !isCorrect;
    const isCorrectAnswer = showResult && isCorrect;

    let backgroundColor = theme.colors?.surface || '#F5F5F5';
    let borderColor = theme.colors?.border || '#E0E0E0';
    let textColor = theme.colors?.text || '#000000';
    let borderWidth = 2;

    if (isSelected && !showResult) {
      borderColor = theme.colors?.primary || '#007AFF';
      backgroundColor = '#E3F2FD'; // Light blue
    } else if (isWrong) {
      backgroundColor = '#FFEBEE'; // Light red
      borderColor = theme.colors?.error || '#F44336';
      textColor = theme.colors?.error || '#F44336';
    } else if (isCorrectAnswer) {
      backgroundColor = '#E8F5E8'; // Light green
      borderColor = theme.colors?.success || '#4CAF50';
      textColor = theme.colors?.success || '#4CAF50';
    }

    return (
      <Animated.View
        key={index}
        style={{
          transform: [
            { translateX: isWrong ? shakeAnim : 0 },
            { scale: isSelected && showResult ? scaleAnim : 1 },
          ],
        }}
      >
        <TouchableOpacity
          style={[styles.option, { backgroundColor, borderColor, borderWidth }]}
          onPress={() => handleAnswerSelect(index)}
          disabled={showResult || selectedAnswer !== null}
          activeOpacity={0.7}
        >
          <View style={styles.optionContent}>
            <View style={styles.optionLabel}>
              <Text style={[styles.optionLabelText, { color: textColor }]}>
                {String.fromCharCode(65 + index)}
              </Text>
            </View>
            <Text style={[styles.optionText, { color: textColor }]}>
              {option}
            </Text>
          </View>

          {showResult && (isSelected || isCorrectAnswer) && (
            <View style={styles.resultIcon}>
              {isCorrectAnswer ? (
                <CheckCircle
                  size={24}
                  color={theme.colors?.success || '#4CAF50'}
                />
              ) : (
                <XCircle size={24} color={theme.colors?.error || '#F44336'} />
              )}
            </View>
          )}
        </TouchableOpacity>
      </Animated.View>
    );
  };

  // Render result feedback
  const renderResultFeedback = () => {
    if (!showResult || selectedAnswer === null) return null;

    const isCorrect = selectedAnswer === correctIndex;
    const canRetry = !isCorrect && attempts < max_attempts;

    return (
      <Animated.View style={[styles.resultCard, { opacity: fadeAnim }]}>
        <View style={styles.resultHeader}>
          <View style={styles.resultIcon}>
            {isCorrect ? (
              <CheckCircle
                size={32}
                color={theme.colors?.success || '#4CAF50'}
              />
            ) : (
              <XCircle size={32} color={theme.colors?.error || '#F44336'} />
            )}
          </View>
          <Text
            style={[
              styles.resultTitle,
              {
                color: isCorrect
                  ? theme.colors?.success || '#4CAF50'
                  : theme.colors?.error || '#F44336',
              },
            ]}
          >
            {isCorrect ? 'Correct!' : 'Incorrect'}
          </Text>
        </View>

        <View style={styles.resultStats}>
          <View style={styles.statItem}>
            <Clock size={16} color={theme.colors?.textSecondary || '#666666'} />
            <Text style={styles.statText}>{Math.ceil(timeSpent)}s</Text>
          </View>
          <View style={styles.statItem}>
            <Target
              size={16}
              color={theme.colors?.textSecondary || '#666666'}
            />
            <Text style={styles.statText}>
              Attempt {attempts}/{max_attempts}
            </Text>
          </View>
        </View>

        {!isCorrect && (
          <Text style={styles.correctAnswerText}>
            Correct answer: {String.fromCharCode(65 + correctIndex)}.{' '}
            {options[correctIndex]}
          </Text>
        )}

        {rationale && (
          <View style={styles.explanationContainer}>
            {!showExplanation ? (
              <Button
                title="Show Explanation"
                onPress={handleShowExplanation}
                variant="secondary"
                style={styles.explanationButton}
              />
            ) : (
              <View style={styles.explanation}>
                <Text style={styles.explanationTitle}>Explanation</Text>
                <Text style={styles.explanationText}>{rationale}</Text>
              </View>
            )}
          </View>
        )}

        <View style={styles.resultActions}>
          {canRetry ? (
            <Button
              title={`Try Again (${max_attempts - attempts} left)`}
              onPress={handleRetry}
              variant="secondary"
              style={styles.retryButton}
            />
          ) : (
            <Button
              title="Continue"
              onPress={handleContinue}
              loading={isLoading}
              style={styles.continueButton}
            />
          )}
        </View>
      </Animated.View>
    );
  };

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Multiple Choice Question</Text>
        {difficulty && (
          <View
            style={[
              styles.difficultyBadge,
              { backgroundColor: getDifficultyColor(difficulty, theme) },
            ]}
          >
            <Text style={styles.difficultyText}>
              {difficulty.toUpperCase()}
            </Text>
          </View>
        )}
      </View>

      {/* Learning objective */}
      {learning_objective && (
        <Card style={styles.objectiveCard}>
          <Text style={styles.objectiveLabel}>Learning Objective</Text>
          <Text style={styles.objectiveText}>{learning_objective}</Text>
        </Card>
      )}

      {/* Question */}
      <Card style={styles.questionCard}>
        <Text style={styles.question}>{questionText}</Text>
      </Card>

      {/* Options */}
      <View style={styles.optionsContainer}>{options.map(renderOption)}</View>

      {/* Result feedback */}
      {renderResultFeedback()}
    </Animated.View>
  );
}

// Helper function to get difficulty color
const getDifficultyColor = (difficulty: string, theme: any) => {
  switch (difficulty) {
    case 'easy':
      return theme.colors?.success || '#4CAF50';
    case 'medium':
      return theme.colors?.warning || '#FF9800';
    case 'hard':
      return theme.colors?.error || '#F44336';
    default:
      return theme.colors?.textSecondary || '#666666';
  }
};

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors?.background || '#FFFFFF',
      padding: theme.spacing?.lg || 16,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing?.lg || 16,
    },
    title: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors?.text || '#000000',
      flex: 1,
    },
    difficultyBadge: {
      paddingHorizontal: theme.spacing?.sm || 8,
      paddingVertical: 4,
      borderRadius: 12,
    },
    difficultyText: {
      fontSize: 10,
      fontWeight: 'bold',
      color: '#FFFFFF',
      letterSpacing: 0.5,
    },
    objectiveCard: {
      padding: theme.spacing?.md || 12,
      marginBottom: theme.spacing?.md || 12,
      backgroundColor: theme.colors?.primaryLight || '#E3F2FD',
    },
    objectiveLabel: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.colors?.primary || '#007AFF',
      marginBottom: 4,
      textTransform: 'uppercase',
      letterSpacing: 0.5,
    },
    objectiveText: {
      fontSize: 14,
      color: theme.colors?.text || '#000000',
      lineHeight: 18,
    },
    questionCard: {
      padding: theme.spacing?.lg || 16,
      marginBottom: theme.spacing?.lg || 16,
    },
    question: {
      fontSize: 18,
      lineHeight: 26,
      color: theme.colors?.text || '#000000',
    },
    optionsContainer: {
      marginBottom: theme.spacing?.lg || 16,
    },
    option: {
      padding: theme.spacing?.md || 12,
      marginBottom: theme.spacing?.md || 12,
      borderRadius: 12,
      borderWidth: 2,
    },
    optionContent: {
      flexDirection: 'row',
      alignItems: 'center',
      flex: 1,
    },
    optionLabel: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: theme.colors?.border || '#E0E0E0',
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: theme.spacing?.md || 12,
    },
    optionLabelText: {
      fontSize: 14,
      fontWeight: 'bold',
    },
    optionText: {
      fontSize: 16,
      lineHeight: 22,
      flex: 1,
    },
    resultIcon: {
      marginLeft: theme.spacing?.sm || 8,
    },
    resultCard: {
      padding: theme.spacing?.lg || 16,
      backgroundColor: theme.colors?.surface || '#F8F9FA',
      borderRadius: 12,
      marginTop: theme.spacing?.lg || 16,
    },
    resultHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: theme.spacing?.md || 12,
    },
    resultTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      marginLeft: theme.spacing?.md || 12,
    },
    resultStats: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginBottom: theme.spacing?.md || 12,
      paddingVertical: theme.spacing?.sm || 8,
      backgroundColor: theme.colors?.background || '#FFFFFF',
      borderRadius: 8,
    },
    statItem: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    statText: {
      fontSize: 14,
      color: theme.colors?.textSecondary || '#666666',
      marginLeft: 4,
      fontWeight: '500',
    },
    correctAnswerText: {
      fontSize: 14,
      color: theme.colors?.textSecondary || '#666666',
      marginBottom: theme.spacing?.md || 12,
      padding: theme.spacing?.sm || 8,
      backgroundColor: theme.colors?.background || '#FFFFFF',
      borderRadius: 6,
      fontStyle: 'italic',
    },
    explanationContainer: {
      marginBottom: theme.spacing?.md || 12,
    },
    explanationButton: {
      alignSelf: 'flex-start',
    },
    explanation: {
      padding: theme.spacing?.md || 12,
      backgroundColor: theme.colors?.background || '#FFFFFF',
      borderRadius: 8,
      borderLeftWidth: 4,
      borderLeftColor: theme.colors?.primary || '#007AFF',
    },
    explanationTitle: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors?.primary || '#007AFF',
      marginBottom: theme.spacing?.sm || 8,
    },
    explanationText: {
      fontSize: 14,
      lineHeight: 20,
      color: theme.colors?.text || '#000000',
    },
    resultActions: {
      marginTop: theme.spacing?.md || 12,
    },
    retryButton: {
      width: '100%',
    },
    continueButton: {
      width: '100%',
    },
  });
