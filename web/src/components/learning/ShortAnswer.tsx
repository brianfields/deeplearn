'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  RotateCcw,
  Edit3,
  HelpCircle,
  Star,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { ShortAnswerProps, ShortAnswerQuestion } from '@/types/components'

type FeedbackType = 'excellent' | 'good' | 'needs_improvement' | 'incomplete'

interface AnswerFeedback {
  type: FeedbackType
  score: number
  strengths: string[]
  improvements: string[]
  keyConceptsCovered: string[]
  overallComment: string
}

export default function ShortAnswer({
  assessment,
  onComplete,
  isLoading = false
}: ShortAnswerProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [showHint, setShowHint] = useState(false)
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [responses, setResponses] = useState<any[]>([])
  const [allFeedback, setAllFeedback] = useState<any[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const currentQuestion = assessment.questions[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex === assessment.questions.length - 1

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [answer])

  const generateFeedback = (answer: string, question: ShortAnswerQuestion): AnswerFeedback => {
    // This would normally call your AI service for evaluation
    // For now, we'll simulate feedback based on answer length and key concepts
    const wordCount = answer.split(/\s+/).filter(word => word.length > 0).length

    // Extract key concepts from expected_elements string
    const expectedElements = question.expected_elements.toLowerCase()
    const keyTerms = [question.target_concept.toLowerCase()]

    // Simple heuristic: check if answer contains target concept and some keywords from expected elements
    const answerLower = answer.toLowerCase()
    const conceptMentioned = answerLower.includes(question.target_concept.toLowerCase())
    const hasSubstantialContent = wordCount >= 20
    const seemsRelevant = expectedElements.split(' ').slice(0, 5).some(word =>
      word.length > 3 && answerLower.includes(word)
    )

    let type: FeedbackType
    let score: number
    let strengths: string[] = []
    let improvements: string[] = []
    let overallComment: string

    if (wordCount < 10) {
      type = 'incomplete'
      score = 2
      improvements = [
        'Provide more detailed explanation',
        'Include specific examples',
        'Address all parts of the question'
      ]
      overallComment = 'Your answer needs more development. Try to elaborate on your main points.'
    } else if (conceptMentioned && hasSubstantialContent && seemsRelevant) {
      type = 'excellent'
      score = 5
      strengths = [
        'Addresses the target concept',
        'Well-structured response',
        'Clear understanding demonstrated'
      ]
      overallComment = 'Excellent work! You\'ve demonstrated a strong understanding of the topic.'
    } else if (conceptMentioned || seemsRelevant) {
      type = 'good'
      score = 4
      strengths = ['Good understanding shown', 'Clear explanations']
      improvements = ['Consider addressing the core concept more directly']
      overallComment = 'Good response! You could strengthen it by focusing more on the key concepts.'
    } else {
      type = 'needs_improvement'
      score = 3
      strengths = ['Shows some understanding']
      improvements = [
        'Focus on the target concept',
        'Include expected elements from the question',
        'Connect ideas more explicitly'
      ]
      overallComment = 'Your answer shows some understanding but could be improved.'
    }

    return {
      type,
      score,
      strengths,
      improvements,
      keyConceptsCovered: conceptMentioned ? [question.target_concept] : [],
      overallComment
    }
  }

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) return

    setIsSubmitting(true)

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500))

    const answerFeedback = generateFeedback(answer, currentQuestion)
    setFeedback(answerFeedback)
    setIsSubmitting(false)
  }

  const handleNextQuestion = () => {
    if (!feedback) return

    const response = {
      questionId: currentQuestion.number.toString(),
      question: currentQuestion.question,
      answer: answer,
      feedback: feedback
    }

    setResponses(prev => [...prev, response])
    setAllFeedback(prev => [...prev, feedback])

    if (isLastQuestion) {
      onComplete({
        componentType: 'short_answer_question',
        timeSpent: 0,
        completed: true,
        data: {
          responses: [...responses, response],
          feedback: [...allFeedback, feedback]
        }
      })
    } else {
      setCurrentQuestionIndex(prev => prev + 1)
      setAnswer('')
      setFeedback(null)
      setShowHint(false)
    }
  }

  const handleRetry = () => {
    setAnswer('')
    setFeedback(null)
    setShowHint(false)
  }

  const getFeedbackIcon = (type: FeedbackType) => {
    switch (type) {
      case 'excellent':
        return <Star className="w-5 h-5 text-yellow-500" />
      case 'good':
        return <ThumbsUp className="w-5 h-5 text-green-500" />
      case 'needs_improvement':
        return <ThumbsDown className="w-5 h-5 text-orange-500" />
      case 'incomplete':
        return <AlertCircle className="w-5 h-5 text-red-500" />
    }
  }

  const getFeedbackColor = (type: FeedbackType) => {
    switch (type) {
      case 'excellent':
        return 'bg-yellow-50 border-yellow-200'
      case 'good':
        return 'bg-green-50 border-green-200'
      case 'needs_improvement':
        return 'bg-orange-50 border-orange-200'
      case 'incomplete':
        return 'bg-red-50 border-red-200'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 5) return 'text-yellow-600'
    if (score >= 4) return 'text-green-600'
    if (score >= 3) return 'text-orange-600'
    return 'text-red-600'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Edit3 className="w-5 h-5 text-indigo-600" />
            <span className="text-sm font-medium text-indigo-600">Reflect</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
            Question {currentQuestionIndex + 1} of {assessment.questions.length}
          </h1>
          <p className="text-gray-600 text-sm">
            Write a thoughtful response
          </p>
        </motion.div>

        {/* Question */}
        <motion.div
          key={currentQuestionIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="p-6 mb-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 leading-relaxed">
              {currentQuestion.question}
            </h2>

            <div className="mb-4 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
              <p className="text-indigo-800 text-sm leading-relaxed">
                <strong>Purpose:</strong> {currentQuestion.purpose}
              </p>
            </div>

            {/* Target Concept */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Focus on this concept:</h3>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary" className="text-xs">
                  {currentQuestion.target_concept}
                </Badge>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Answer Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <Card className="p-6 bg-white/90 backdrop-blur-sm border-0 shadow-lg">
            <label htmlFor="answer" className="block text-sm font-medium text-gray-700 mb-2">
              Your Answer
            </label>
            <Textarea
              ref={textareaRef}
              id="answer"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Write your answer here..."
              className="min-h-[120px] resize-none bg-white/80 border-gray-200 focus:border-indigo-400"
              disabled={!!feedback}
            />
            <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
              <span>{answer.split(/\s+/).filter(word => word.length > 0).length} words</span>
              <span>Aim for at least 50 words</span>
            </div>
          </Card>
        </motion.div>

        {/* Hint */}
        {!feedback && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-6"
          >
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
                                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <Lightbulb className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-blue-800 font-medium mb-2">Hint</p>
                          <p className="text-blue-700 text-sm mb-2">
                            <strong>Purpose:</strong> {currentQuestion.purpose}
                          </p>
                          <p className="text-blue-700 text-sm mb-2">
                            <strong>Focus on:</strong> {currentQuestion.target_concept}
                          </p>
                          <p className="text-blue-700 text-sm">
                            <strong>Consider including:</strong> {currentQuestion.expected_elements}
                          </p>
                        </div>
                      </div>
                    </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Feedback */}
        <AnimatePresence>
          {feedback && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6"
            >
              <Card className={`p-6 ${getFeedbackColor(feedback.type)} border-0 shadow-lg`}>
                <div className="flex items-start gap-3 mb-4">
                  {getFeedbackIcon(feedback.type)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">
                        {feedback.type.charAt(0).toUpperCase() + feedback.type.slice(1).replace('_', ' ')}
                      </h3>
                      <span className={`text-lg font-bold ${getScoreColor(feedback.score)}`}>
                        {feedback.score}/5
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm">{feedback.overallComment}</p>
                  </div>
                </div>

                {/* Strengths */}
                {feedback.strengths.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Strengths
                    </h4>
                    <ul className="space-y-1">
                      {feedback.strengths.map((strength, index) => (
                        <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                          <div className="w-1 h-1 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Improvements */}
                {feedback.improvements.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-600" />
                      Areas for improvement
                    </h4>
                    <ul className="space-y-1">
                      {feedback.improvements.map((improvement, index) => (
                        <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                          <div className="w-1 h-1 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                          {improvement}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Key Concepts Covered */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Target concept coverage:</h4>
                  <div className="flex flex-wrap gap-2">
                    <Badge
                      variant={feedback.keyConceptsCovered.includes(currentQuestion.target_concept) ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {currentQuestion.target_concept}
                      {feedback.keyConceptsCovered.includes(currentQuestion.target_concept) && (
                        <CheckCircle className="w-3 h-3 ml-1" />
                      )}
                    </Badge>
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
          {!feedback ? (
            <Button
              onClick={handleSubmitAnswer}
              disabled={!answer.trim() || isSubmitting}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-3 text-base font-medium"
            >
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Evaluating...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Send className="w-4 h-4" />
                  Submit Answer
                </div>
              )}
            </Button>
          ) : (
            <div className="flex gap-3 w-full">
              {feedback.type === 'incomplete' || feedback.type === 'needs_improvement' ? (
                <Button
                  onClick={handleRetry}
                  variant="outline"
                  className="flex-1 bg-white/80 border-gray-200 hover:bg-white/90"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
              ) : null}
              <Button
                onClick={handleNextQuestion}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 text-base font-medium"
              >
                {isLastQuestion ? 'Complete' : 'Next Question'}
              </Button>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}