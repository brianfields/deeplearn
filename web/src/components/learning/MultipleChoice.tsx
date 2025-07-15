'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, ArrowRight, RotateCcw, Trophy, HelpCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import type { MultipleChoiceProps } from '@/types/components'

interface MultipleChoiceQuestion {
  type: 'multiple_choice_question'
  number: number
  title: string
  question: string
  choices: Record<string, string>
  correct_answer: string
  justifications?: Record<string, string>
  target_concept?: string
  purpose?: string
  difficulty: number
  tags?: string
}

export default function MultipleChoice({
  quiz,
  onComplete,
  isLoading = false
}: MultipleChoiceProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [showHint, setShowHint] = useState(false)
  const [results, setResults] = useState<any[]>([])

  useEffect(() => {
    setSelectedAnswer(null)
    setShowResult(false)
    setShowHint(false)
  }, [currentQuestionIndex])

  const currentQuestion = quiz.questions[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex === quiz.questions.length - 1

  const handleSubmit = () => {
    if (!selectedAnswer) return

    const isCorrect = selectedAnswer === currentQuestion.correct_answer
    const result = {
      questionId: currentQuestion.number.toString(),
      question: currentQuestion.question,
      selectedOption: selectedAnswer,
      selectedText: currentQuestion.choices[selectedAnswer],
      isCorrect,
      explanation: currentQuestion.justifications?.[selectedAnswer] || ''
    }

    setResults(prev => [...prev, result])
    setShowResult(true)
  }

  const handleNext = () => {
    if (isLastQuestion) {
      const finalResults = [...results]
      const correctCount = finalResults.filter(r => r.isCorrect).length
      onComplete({
        componentType: 'multiple_choice_question',
        timeSpent: 0,
        completed: true,
        data: {
          correct: correctCount,
          total: finalResults.length,
          details: finalResults
        }
      })
    } else {
      setCurrentQuestionIndex(prev => prev + 1)
    }
  }

    const getOptionStyle = (choiceKey: string) => {
    const isSelected = selectedAnswer === choiceKey

    if (!showResult) {
      return isSelected
        ? 'bg-blue-100 border-blue-500 text-blue-900'
        : 'bg-white border-gray-200 hover:border-gray-300 text-gray-700'
    }

    const isCorrect = choiceKey === currentQuestion.correct_answer

    if (isCorrect) {
      return 'bg-green-100 border-green-500 text-green-900'
    }

    if (isSelected && !isCorrect) {
      return 'bg-red-100 border-red-500 text-red-900'
    }

    return 'bg-gray-50 border-gray-200 text-gray-500'
  }

  const getOptionIcon = (choiceKey: string) => {
    const isSelected = selectedAnswer === choiceKey

    if (!showResult) {
      return isSelected ? (
        <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
          <div className="w-2 h-2 bg-white rounded-full" />
        </div>
      ) : (
        <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />
      )
    }

    const isCorrect = choiceKey === currentQuestion.correct_answer

    if (isCorrect) {
      return (
        <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
          <CheckCircle className="w-3 h-3 text-white" />
        </div>
      )
    }

    if (isSelected && !isCorrect) {
      return (
        <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
          <XCircle className="w-3 h-3 text-white" />
        </div>
      )
    }

    return <div className="w-5 h-5 border-2 border-gray-300 rounded-full opacity-50" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-600">Practice</span>
          </div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                Question {currentQuestionIndex + 1} of {quiz.questions.length}
              </h1>
              <p className="text-gray-600 text-sm">
                {currentQuestion.title}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600 mb-1">Progress</div>
              <Progress value={((currentQuestionIndex + 1) / quiz.questions.length) * 100} className="w-24" />
            </div>
          </div>
        </motion.div>

        {/* Question */}
        <motion.div
          key={currentQuestionIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="p-6 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-6 leading-relaxed">
              {currentQuestion.question}
            </h2>

            {/* Options */}
            <div className="space-y-3">
              {Object.entries(currentQuestion.choices).map(([choiceKey, choiceText], index) => (
                <motion.button
                  key={choiceKey}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => setSelectedAnswer(choiceKey)}
                  disabled={showResult}
                  className={`w-full p-4 rounded-lg border-2 transition-all duration-200 ${getOptionStyle(choiceKey)}`}
                >
                  <div className="flex items-center gap-3">
                    {getOptionIcon(choiceKey)}
                    <span className="text-left text-sm sm:text-base font-medium flex-1">
                      {choiceKey}. {choiceText}
                    </span>
                  </div>
                </motion.button>
              ))}
            </div>
          </Card>
        </motion.div>

                {/* Explanation */}
        <AnimatePresence>
          {showResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6"
            >
              <Card className="p-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
                <div className="flex items-start gap-3">
                  {selectedAnswer === currentQuestion.correct_answer ? (
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {selectedAnswer === currentQuestion.correct_answer
                        ? 'Correct!'
                        : 'Not quite right'}
                    </h3>
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {selectedAnswer && currentQuestion.justifications?.[selectedAnswer] ||
                       'Good attempt! The correct answer is ' + currentQuestion.correct_answer + '.'}
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hint */}
        {currentQuestion.tags && !showResult && (
          <div className="mb-6">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowHint(!showHint)}
              className="bg-white/80 border-gray-200 hover:bg-white/90"
            >
              <HelpCircle className="w-4 h-4 mr-2" />
              {showHint ? 'Hide Hint' : 'Show Hint'}
            </Button>

            <AnimatePresence>
              {showHint && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3"
                >
                  <Card className="p-4 bg-yellow-50 border-yellow-200">
                    <div className="flex items-start gap-2">
                      <HelpCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
                      <p className="text-yellow-800 text-sm">{currentQuestion.tags}</p>
                    </div>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex gap-3"
        >
          {!showResult ? (
            <Button
              onClick={handleSubmit}
              disabled={!selectedAnswer || isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 text-base font-medium"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Checking...
                </div>
              ) : (
                'Submit Answer'
              )}
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 text-base font-medium"
            >
              <div className="flex items-center gap-2">
                {isLastQuestion ? 'Complete' : 'Next Question'}
                <ArrowRight className="w-4 h-4" />
              </div>
            </Button>
          )}
        </motion.div>
      </div>
    </div>
  )
}