'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Trophy,
  Target,
  Clock,
  CheckCircle,
  XCircle,
  RotateCcw,
  ArrowRight,
  Star,
  Medal,
  Award,
  TrendingUp
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

interface QuizQuestion {
  id: string
  question: string
  type: 'multiple_choice' | 'short_answer' | 'true_false'
  options?: string[]
  correct_answer: string | string[]
  explanation: string
  difficulty: 'easy' | 'medium' | 'hard'
  points: number
}

interface PostTopicQuizProps {
  quiz: {
    title?: string
    description?: string
    items: Array<{
      title: string
      type: string
      question: string
      target_concept: string
      difficulty: number
      tags?: string
      // Multiple Choice fields
      choices?: Record<string, string>
      correct_answer?: string
      justifications?: Record<string, string>
      // Short Answer fields
      expected_elements?: string
      // Assessment Dialogue fields
      dialogue_objective?: string
      scaffolding_prompts?: string
      exit_criteria?: string
    }>
    passing_score?: number
    time_limit?: number
  }
  onComplete: (results: QuizResults) => void
  onRetry?: () => void
}

interface QuizResults {
  score: number
  totalQuestions: number
  correctAnswers: number
  timeSpent: number
  passed: boolean
  breakdown: {
    easy: { correct: number; total: number }
    medium: { correct: number; total: number }
    hard: { correct: number; total: number }
  }
  answers: any[]
}

export default function PostTopicQuiz({ quiz, onComplete, onRetry }: PostTopicQuizProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [shortAnswer, setShortAnswer] = useState('')
  const [answers, setAnswers] = useState<any[]>([])
  const [showResult, setShowResult] = useState(false)
  const [quizCompleted, setQuizCompleted] = useState(false)
  const [startTime] = useState(Date.now())
  const [timeLeft, setTimeLeft] = useState(quiz.time_limit || 0)
  const [finalResults, setFinalResults] = useState<QuizResults | null>(null)

  const currentQuestion = quiz.items[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex === quiz.items.length - 1

  const handleQuizComplete = useCallback(() => {
    const timeSpent = Math.round((Date.now() - startTime) / 1000)
    const totalPoints = answers.reduce((sum, answer) => sum + answer.points, 0)
    // Calculate max points from difficulty (using difficulty as base points)
    const maxPoints = quiz.items.reduce((sum, item) => sum + item.difficulty * 10, 0)
    const score = Math.round((totalPoints / maxPoints) * 100)
    const correctAnswers = answers.filter(a => a.isCorrect).length
    const passed = score >= (quiz.passing_score || 70)

    // Calculate breakdown by difficulty
    const breakdown = {
      easy: { correct: 0, total: 0 },
      medium: { correct: 0, total: 0 },
      hard: { correct: 0, total: 0 }
    }

    answers.forEach(answer => {
      const difficulty = answer.difficulty as 'easy' | 'medium' | 'hard'
      breakdown[difficulty].total++
      if (answer.isCorrect) {
        breakdown[difficulty].correct++
      }
    })

    const results: QuizResults = {
      score,
      totalQuestions: quiz.items.length,
      correctAnswers,
      timeSpent,
      passed,
      breakdown,
      answers
    }

    setFinalResults(results)
    setQuizCompleted(true)
    onComplete(results)
  }, [startTime, answers, quiz.items, quiz.passing_score, onComplete])

  // Timer effect
  useEffect(() => {
    if (quiz.time_limit && timeLeft > 0 && !quizCompleted) {
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleQuizComplete()
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [timeLeft, quizCompleted, quiz.time_limit, handleQuizComplete])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleAnswerSelect = (answer: string) => {
    if (showResult) return

    if (currentQuestion.type === 'multiple_choice' || currentQuestion.type === 'true_false') {
      setSelectedAnswer(answer)
    }
  }

  const handleSubmitAnswer = () => {
    let userAnswer = selectedAnswer
    if (currentQuestion.type === 'short_answer') {
      userAnswer = shortAnswer.trim()
    }

    if (!userAnswer) return

    const isCorrect = Array.isArray(currentQuestion.correct_answer)
      ? currentQuestion.correct_answer.includes(userAnswer)
      : currentQuestion.correct_answer === userAnswer

    const answerData = {
              questionId: (currentQuestionIndex + 1).toString(),
      question: currentQuestion.question,
      userAnswer,
      correctAnswer: currentQuestion.correct_answer,
      isCorrect,
              difficulty: currentQuestion.difficulty > 3 ? 'hard' as const :
                   currentQuestion.difficulty > 1 ? 'medium' as const : 'easy' as const,
      points: isCorrect ? currentQuestion.difficulty * 10 : 0,
      explanation: currentQuestion.justifications ?
        Object.values(currentQuestion.justifications).join(' ') :
        currentQuestion.target_concept
    }

    setAnswers(prev => [...prev, answerData])
    setShowResult(true)
  }

  const handleNextQuestion = () => {
    if (isLastQuestion) {
      handleQuizComplete()
    } else {
      setCurrentQuestionIndex(prev => prev + 1)
      setSelectedAnswer(null)
      setShortAnswer('')
      setShowResult(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-blue-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <Trophy className="w-8 h-8 text-yellow-500" />
    if (score >= 80) return <Medal className="w-8 h-8 text-blue-500" />
    if (score >= 70) return <Award className="w-8 h-8 text-orange-500" />
    return <Target className="w-8 h-8 text-gray-500" />
  }

  if (quizCompleted && finalResults) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-100 p-4">
        <div className="max-w-2xl mx-auto">
          {/* Results Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="mb-4">
              {getScoreIcon(finalResults.score)}
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Quiz Complete!
            </h1>
            <p className="text-gray-600">
              {finalResults.passed ? 'Congratulations! You passed!' : 'Keep practicing to improve your score!'}
            </p>
          </motion.div>

          {/* Score Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-8 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg text-center">
              <div className="mb-6">
                <div className={`text-6xl font-bold ${getScoreColor(finalResults.score)} mb-2`}>
                  {finalResults.score}%
                </div>
                <div className="text-gray-600">
                  {finalResults.correctAnswers} out of {finalResults.totalQuestions} questions correct
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center">
                  <Clock className="w-5 h-5 mx-auto mb-1 text-gray-500" />
                  <div className="text-sm text-gray-600">Time</div>
                  <div className="font-semibold">{formatTime(finalResults.timeSpent)}</div>
                </div>
                <div className="text-center">
                  <TrendingUp className="w-5 h-5 mx-auto mb-1 text-gray-500" />
                  <div className="text-sm text-gray-600">Status</div>
                  <Badge variant={finalResults.passed ? "default" : "secondary"}>
                    {finalResults.passed ? 'Passed' : 'Not Passed'}
                  </Badge>
                </div>
              </div>

              <div className="text-sm text-gray-600 mb-4">
                Minimum passing score: {quiz.passing_score}%
              </div>

              <Progress value={finalResults.score} className="mb-4" />
            </Card>
          </motion.div>

          {/* Breakdown by Difficulty */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Breakdown</h3>
              <div className="space-y-4">
                {Object.entries(finalResults.breakdown).map(([difficulty, data]) => (
                  <div key={difficulty} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={difficulty === 'easy' ? 'secondary' : difficulty === 'medium' ? 'default' : 'destructive'}
                        className="capitalize"
                      >
                        {difficulty}
                      </Badge>
                      <span className="text-sm text-gray-600">
                        {data.correct}/{data.total} correct
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {data.total > 0 ? Math.round((data.correct / data.total) * 100) : 0}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="flex gap-3"
          >
            {onRetry && !finalResults.passed && (
              <Button
                onClick={onRetry}
                variant="outline"
                className="flex-1 bg-white/80 border-gray-200 hover:bg-white/90"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            )}
            <Button
              onClick={() => window.history.back()}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Continue Learning
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-100 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Trophy className="w-5 h-5 text-orange-600" />
            <span className="text-sm font-medium text-orange-600">Quiz</span>
          </div>
          <div className="flex items-center justify-between mb-4">
            <div>
                              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                  {quiz.title || 'Quiz'}
                </h1>
              <p className="text-gray-600 text-sm">
                Question {currentQuestionIndex + 1} of {quiz.items.length}
              </p>
            </div>
            <div className="text-right">
              {quiz.time_limit && (
                <div className="text-sm text-gray-600 mb-1">Time Left</div>
              )}
              {quiz.time_limit && (
                <div className={`font-bold ${timeLeft < 60 ? 'text-red-600' : 'text-gray-900'}`}>
                  {formatTime(timeLeft)}
                </div>
              )}
            </div>
          </div>
          <Progress value={(currentQuestionIndex / quiz.items.length) * 100} />
        </motion.div>

        {/* Question */}
        <motion.div
          key={currentQuestionIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="p-6 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
            <div className="flex items-center gap-2 mb-4">
              <Badge variant={currentQuestion.difficulty <= 1 ? 'secondary' : currentQuestion.difficulty <= 3 ? 'default' : 'destructive'}>
                {currentQuestion.difficulty}
              </Badge>
              <span className="text-sm text-gray-600">{currentQuestion.difficulty * 10} points</span>
            </div>

            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-6 leading-relaxed">
              {currentQuestion.question}
            </h2>

            {/* Question Input */}
            {currentQuestion.type === 'short_answer' ? (
              <textarea
                value={shortAnswer}
                onChange={(e) => setShortAnswer(e.target.value)}
                placeholder="Enter your answer..."
                className="w-full p-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 disabled:bg-gray-50"
                rows={4}
                disabled={showResult}
              />
            ) : (
              <div className="space-y-3">
                {Object.entries(currentQuestion.choices || {}).map(([key, option]) => (
                                      <button
                      key={key}
                                          onClick={() => setSelectedAnswer(key)}
                    disabled={showResult}
                    className={`w-full p-4 rounded-lg border-2 transition-all duration-200 text-left ${
                      selectedAnswer === option
                        ? 'bg-orange-100 border-orange-500 text-orange-900'
                        : 'bg-white border-gray-200 hover:border-gray-300 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        selectedAnswer === option
                          ? 'bg-orange-500 border-orange-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedAnswer === option && (
                          <div className="w-2 h-2 bg-white rounded-full" />
                        )}
                      </div>
                      <span className="text-sm sm:text-base font-medium">{option}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </motion.div>

        {/* Answer Feedback */}
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
                  {answers[answers.length - 1]?.isCorrect ? (
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {answers[answers.length - 1]?.isCorrect ? 'Correct!' : 'Incorrect'}
                    </h3>
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {currentQuestion.expected_elements || currentQuestion.target_concept}
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex gap-3"
        >
          {!showResult ? (
            <Button
              onClick={handleSubmitAnswer}
              disabled={
                (currentQuestion.type === 'short_answer' && !shortAnswer.trim()) ||
                (currentQuestion.type !== 'short_answer' && !selectedAnswer)
              }
              className="flex-1 bg-orange-600 hover:bg-orange-700 text-white py-3 text-base font-medium"
            >
              Submit Answer
            </Button>
          ) : (
            <Button
              onClick={handleNextQuestion}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 text-base font-medium"
            >
              {isLastQuestion ? 'Finish Quiz' : 'Next Question'}
            </Button>
          )}
        </motion.div>
      </div>
    </div>
  )
}