/**
 * MultipleChoice Component - Interactive Knowledge Assessment
 *
 * Handles multiple-choice questions that test user understanding
 * after they've consumed educational content.
 *
 * This is a simplified version for the modular architecture.
 * Full implementation will be completed during Phase 3 integration.
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Button, Card } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { CheckCircle, XCircle } from 'lucide-react-native';
import type { ComponentState } from '../models';

interface MultipleChoiceProps {
  component: ComponentState;
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

export default function MultipleChoice({
  component,
  onComplete,
  isLoading = false,
}: MultipleChoiceProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);

  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

  // Extract content from component
  const content = component.content || {};
  const question =
    content.question || content.stem || 'Question will be displayed here.';
  const options = content.options ||
    content.choices || ['Option A', 'Option B', 'Option C', 'Option D'];
  const correctAnswer =
    content.correct_answer || content.correct_answer_index || 0;

  const handleAnswerSelect = (answer: string, index: number) => {
    if (showResult) return;

    setSelectedAnswer(answer);
    setShowResult(true);

    const isCorrect = index === correctAnswer || answer === correctAnswer;

    // Complete after a short delay
    setTimeout(() => {
      onComplete({
        componentId: component.id,
        userAnswer: answer,
        isCorrect,
        timeSpent: 30, // Placeholder
      });
    }, 2000);
  };

  const renderOption = (option: string, index: number) => {
    const isSelected = selectedAnswer === option;
    const isCorrect = index === correctAnswer || option === correctAnswer;

    let backgroundColor = theme.colors?.surface || '#F5F5F5';
    let borderColor = theme.colors?.border || '#E0E0E0';
    let textColor = theme.colors?.text || '#000000';

    if (showResult && isSelected) {
      if (isCorrect) {
        backgroundColor = '#E8F5E8';
        borderColor = '#4CAF50';
        textColor = '#2E7D32';
      } else {
        backgroundColor = '#FFEBEE';
        borderColor = '#F44336';
        textColor = '#C62828';
      }
    }

    return (
      <TouchableOpacity
        key={index}
        style={[styles.option, { backgroundColor, borderColor }]}
        onPress={() => handleAnswerSelect(option, index)}
        disabled={showResult}
      >
        <Text style={[styles.optionText, { color: textColor }]}>
          {String.fromCharCode(65 + index)}. {option}
        </Text>
        {showResult && isSelected && (
          <View style={styles.resultIcon}>
            {isCorrect ? (
              <CheckCircle size={24} color="#4CAF50" />
            ) : (
              <XCircle size={24} color="#F44336" />
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Multiple Choice Question</Text>
      </View>

      <Card style={styles.questionCard}>
        <Text style={styles.question}>{question}</Text>
      </Card>

      <View style={styles.optionsContainer}>
        {Array.isArray(options)
          ? options.map(renderOption)
          : Object.entries(options).map(([_key, value], index) =>
              renderOption(value as string, index)
            )}
      </View>

      <Text style={styles.placeholder}>
        🚧 Multiple Choice Component
        {'\n\n'}
        This component will provide interactive assessment with:
        {'\n'}• Immediate feedback
        {'\n'}• Detailed explanations
        {'\n'}• Progress tracking
        {'\n'}• Haptic feedback
        {'\n\n'}
        Full implementation pending Phase 3 integration.
      </Text>

      {showResult && (
        <View style={styles.footer}>
          <Button
            title="Continue"
            onPress={() => {
              /* Will be handled by timeout */
            }}
            loading={isLoading}
            style={styles.continueButton}
          />
        </View>
      )}
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors?.background || '#FFFFFF',
      padding: theme.spacing?.lg || 16,
    },
    header: {
      marginBottom: theme.spacing?.lg || 16,
    },
    title: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors?.text || '#000000',
      textAlign: 'center',
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
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: theme.spacing?.md || 12,
      marginBottom: theme.spacing?.sm || 8,
      borderRadius: 8,
      borderWidth: 2,
    },
    optionText: {
      fontSize: 16,
      flex: 1,
    },
    resultIcon: {
      marginLeft: theme.spacing?.sm || 8,
    },
    placeholder: {
      fontSize: 14,
      color: theme.colors?.textSecondary || '#666666',
      textAlign: 'center',
      lineHeight: 20,
      marginBottom: theme.spacing?.lg || 16,
    },
    footer: {
      marginTop: 'auto',
    },
    continueButton: {
      width: '100%',
    },
  });
