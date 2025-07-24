/**
 * Multiple Choice Component for React Native
 *
 * A mobile-optimized MCQ component with touch interactions,
 * animations, and instant feedback
 */

import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Vibration,
  Platform
} from 'react-native'
import Animated, {
  FadeIn,
  FadeOut,
  SlideInUp,
  SlideInDown,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
  ZoomIn,
  ZoomOut
} from 'react-native-reanimated'
import * as Haptics from 'expo-haptics'

// Icons
import {
  CheckCircle,
  XCircle,
  ArrowRight,
  RotateCcw,
  HelpCircle,
  Lightbulb
} from 'lucide-react-native'

// Components
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Progress } from '@/components/ui/Progress'

// Theme & Types
import { colors, spacing, typography, shadows, responsive } from '@/utils/theme'
import type { MultipleChoiceProps, MultipleChoiceQuestion } from '@/types'

interface ChoiceItemProps {
  letter: string
  text: string
  isSelected: boolean
  isCorrect?: boolean
  isIncorrect?: boolean
  onPress: () => void
  disabled?: boolean
}

const ChoiceItem: React.FC<ChoiceItemProps> = ({
  letter,
  text,
  isSelected,
  isCorrect,
  isIncorrect,
  onPress,
  disabled = false
}) => {
  const scaleValue = useSharedValue(1)
  const colorValue = useSharedValue(0)

  useEffect(() => {
    if (isSelected) {
      scaleValue.value = withSpring(0.98, { damping: 15 })
    } else {
      scaleValue.value = withSpring(1)
    }

    if (isCorrect) {
      colorValue.value = withTiming(1)
    } else if (isIncorrect) {
      colorValue.value = withTiming(-1)
    } else {
      colorValue.value = withTiming(0)
    }
  }, [isSelected, isCorrect, isIncorrect])

  const animatedStyle = useAnimatedStyle(() => {
    let backgroundColor = colors.surface
    let borderColor = colors.border

    if (colorValue.value === 1) {
      backgroundColor = `${colors.success}20`
      borderColor = colors.success
    } else if (colorValue.value === -1) {
      backgroundColor = `${colors.error}20`
      borderColor = colors.error
    } else if (isSelected) {
      backgroundColor = `${colors.primary}10`
      borderColor = colors.primary
    }

    return {
      transform: [{ scale: scaleValue.value }],
      backgroundColor,
      borderColor,
    }
  })

  const letterStyle = useAnimatedStyle(() => {
    let backgroundColor = colors.border
    let color = colors.text

    if (colorValue.value === 1) {
      backgroundColor = colors.success
      color = colors.surface
    } else if (colorValue.value === -1) {
      backgroundColor = colors.error
      color = colors.surface
    } else if (isSelected) {
      backgroundColor = colors.primary
      color = colors.surface
    }

    return {
      backgroundColor,
      color,
    }
  })

  const handlePress = () => {
    if (!disabled) {
      // Haptic feedback
      if (Platform.OS === 'ios') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)
      } else {
        Vibration.vibrate(10)
      }
      onPress()
    }
  }

  return (
    <TouchableOpacity onPress={handlePress} disabled={disabled} activeOpacity={0.8}>
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
  )
}

export default function MultipleChoice({
  question,
  onComplete,
  isLoading = false
}: MultipleChoiceProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [showResult, setShowResult] = useState(false)

  // Convert choices object to array for easier index-based access
  const choicesArray = Object.entries(question.choices)

  // Generate letter for display (A, B, C, D, etc.)
  const getChoiceLetter = (index: number) => String.fromCharCode(65 + index) // 65 is 'A'

  // Reset state when question changes
  useEffect(() => {
    setSelectedAnswer(null)
    setShowResult(false)
  }, [question])

  const handleAnswerSelect = (answerIndex: number) => {
    if (showResult || isLoading) return

    setSelectedAnswer(answerIndex)

    // Auto-submit the answer
    setTimeout(() => {
      handleSubmit(answerIndex)
    }, 300) // Small delay for visual feedback
  }

  const handleSubmit = (answerIndex: number) => {
    if (question.correct_answer_index === undefined) return

    const isCorrect = answerIndex === question.correct_answer_index
    const selectedChoice = choicesArray[answerIndex]
    const selectedLetter = getChoiceLetter(answerIndex)

    const result = {
      questionId: question.number?.toString() || '0',
      question: question.question,
      selectedOption: selectedLetter, // For backward compatibility with results
      selectedText: selectedChoice[1], // The choice text
      isCorrect,
      explanation: question.justifications[selectedChoice[0]] || '' // Use original letter key for justifications
    }

    setShowResult(true)

    // Haptic feedback for result
    if (Platform.OS === 'ios') {
      Haptics.impactAsync(
        isCorrect
          ? Haptics.ImpactFeedbackStyle.Medium
          : Haptics.ImpactFeedbackStyle.Heavy
      )
    } else {
      Vibration.vibrate(isCorrect ? 50 : [0, 100, 50, 100])
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
            details: [result]
          }
        })
      }, 1500) // Show correct feedback briefly then auto-proceed
    }
    // For incorrect answers, user must press Continue button
  }

  const handleContinue = () => {
    if (selectedAnswer === null) return

    const selectedChoice = choicesArray[selectedAnswer]
    const selectedLetter = getChoiceLetter(selectedAnswer)

    const result = {
      questionId: question.number?.toString() || '0',
      question: question.question,
      selectedOption: selectedLetter,
      selectedText: selectedChoice[1],
      isCorrect: false,
      explanation: question.justifications[selectedChoice[0]] || ''
    }

    onComplete({
      componentType: 'multiple_choice_question',
      timeSpent: 0,
      completed: true,
      data: {
        correct: 0,
        total: 1,
        details: [result]
      }
    })
  }

  if (!question) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>No question available</Text>
        </View>
      </View>
    )
  }

  const isCorrectAnswer = selectedAnswer === question.correct_answer_index
  const isIncorrectAnswer = showResult && selectedAnswer !== null && !isCorrectAnswer

  return (
    <View style={styles.container}>
      {/* Question */}
      <Animated.View
        key={question.number || 'question'}
        entering={SlideInUp}
        style={styles.content}
      >
        <Card style={styles.questionCard}>
          <Text style={styles.questionText}>
            {question.question}
          </Text>
        </Card>

        {/* Choices */}
        <View style={styles.choicesContainer}>
          {choicesArray.map(([letter, text], index) => (
            <Animated.View
              key={index}
              entering={FadeIn.delay(200 + index * 100)}
              style={styles.choiceWrapper}
            >
              <ChoiceItem
                letter={getChoiceLetter(index)}
                text={text}
                isSelected={selectedAnswer === index}
                isCorrect={showResult && index === question.correct_answer_index}
                isIncorrect={showResult && selectedAnswer === index && index !== question.correct_answer_index}
                onPress={() => handleAnswerSelect(index)}
                disabled={showResult || isLoading}
              />
            </Animated.View>
          ))}
        </View>

        {/* Explanation */}
        {showResult && selectedAnswer !== null && question.justifications[choicesArray[selectedAnswer]![0]] && (
          <Animated.View
            entering={SlideInUp.delay(300)}
            style={styles.explanationContainer}
          >
            <Card style={styles.explanationCard}>
              <View style={styles.explanationHeader}>
                <Text style={styles.explanationTitle}>
                  {isCorrectAnswer ? "Correct!" : "Explanation"}
                </Text>
              </View>
              <Text style={styles.explanationText}>
                {question.justifications[choicesArray[selectedAnswer]![0]]}
              </Text>
            </Card>
          </Animated.View>
        )}
      </Animated.View>

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
  )
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

  content: {
    flex: 1,
    padding: spacing.lg,
  },

  questionCard: {
    marginBottom: spacing.lg,
  },

  questionText: {
    fontSize: 18,
    fontWeight: '500' as const,
    lineHeight: 28,
    color: colors.text,
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
    padding: spacing.md,
    borderRadius: 12,
    borderWidth: 2,
    ...shadows.small,
  },

  choiceLetter: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },

  choiceLetterText: {
    fontSize: 16,
    fontWeight: '600' as const,
  },

  choiceText: {
    fontSize: 16,
    fontWeight: '400' as const,
    color: colors.text,
    flex: 1,
    lineHeight: 24,
  },

  resultIcon: {
    marginLeft: spacing.sm,
  },

  explanationContainer: {
    marginBottom: spacing.lg,
  },

  explanationCard: {
    backgroundColor: `${colors.info}05`,
    borderLeftWidth: 4,
    borderLeftColor: colors.info,
  },

  explanationHeader: {
    marginBottom: spacing.sm,
  },

  explanationTitle: {
    fontSize: 16,
    fontWeight: '600' as const,
    color: colors.text,
  },

  explanationText: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 24,
    color: colors.text,
  },

  actionContainer: {
    padding: spacing.lg,
    paddingTop: 0,
  },

  actionButton: {
    ...shadows.medium,
  },
})
