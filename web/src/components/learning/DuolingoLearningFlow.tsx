'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  CheckCircle,
  Trophy,
  Flame,
  Target,
  Clock,
  Zap,
  Star,
  ChevronRight,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

import DidacticSnippet from './DidacticSnippet'
import SocraticDialogue from './SocraticDialogue'
import MultipleChoice from './MultipleChoice'
import ShortAnswer from './ShortAnswer'
import PostTopicQuiz from './PostTopicQuiz'

import { duolingoLearningService } from '@/services/duolingo-learning'
import type { BiteSizedTopicDetail, ComponentType, LearningResults } from '@/types'

interface DuolingoLearningFlowProps {
  topic: BiteSizedTopicDetail
  onComplete: (results: LearningResults) => void
  onBack: () => void
}

// Optimized component ordering for engagement
const COMPONENT_ORDER: ComponentType[] = [
  'didactic_snippet',    // 1. Learn
  'multiple_choice_question', // 2. Quick check
  'short_answer_question',    // 3. Apply
  'socratic_dialogue',        // 4. Explore (if available)
  'post_topic_quiz'          // 5. Master
]

interface ComponentStep {
  type: ComponentType
  components: any[]
  currentIndex: number
  isCompleted: boolean
}

export default function DuolingoLearningFlow({ topic, onComplete, onBack }: DuolingoLearningFlowProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [startTime] = useState(Date.now())
  const [completedSteps, setCompletedSteps] = useState<string[]>([])
  const [interactionResults, setInteractionResults] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [streakCount, setStreakCount] = useState(0)
  const [showCelebration, setShowCelebration] = useState(false)

  // Organize components into steps
  const componentSteps = useMemo((): ComponentStep[] => {
    const steps: ComponentStep[] = []

    for (const componentType of COMPONENT_ORDER) {
      const components = topic.components.filter(c => c.component_type === componentType)
      if (components.length > 0) {
        steps.push({
          type: componentType,
          components,
          currentIndex: 0,
          isCompleted: false
        })
      }
    }

    return steps
  }, [topic.components])

  const currentStep = componentSteps[currentStepIndex]
  const totalSteps = componentSteps.length
  const progress = totalSteps > 0 ? (currentStepIndex / totalSteps) * 100 : 0

  // Load streak count on mount
  useEffect(() => {
    const stats = duolingoLearningService.getCacheStats()
    setStreakCount(stats.currentStreak)
  }, [])

  // Save progress continuously
  useEffect(() => {
    duolingoLearningService.saveTopicProgress(topic.id, {
      currentComponentIndex: currentStepIndex,
      completedComponents: completedSteps,
      timeSpent: Date.now() - startTime,
      interactionResults
    })
  }, [topic.id, currentStepIndex, completedSteps, startTime, interactionResults])

  const handleStepComplete = useCallback((stepType: string, results?: any) => {
    setCompletedSteps(prev => [...prev, stepType])

    if (results) {
      setInteractionResults(prev => [...prev, results])
    }

    // Move to next step or complete
    if (currentStepIndex < componentSteps.length - 1) {
      setCurrentStepIndex(prev => prev + 1)

      // Show mini celebration for good progress
      if (results?.correct !== undefined && results.correct / results.total >= 0.8) {
        setShowCelebration(true)
        setTimeout(() => setShowCelebration(false), 1500)
      }
    } else {
      handleTopicComplete()
    }
  }, [currentStepIndex, componentSteps.length])

  const handleTopicComplete = useCallback(async () => {
    const timeSpent = Math.round((Date.now() - startTime) / 1000)

    // Calculate final score
    let finalScore = 100
    if (interactionResults.length > 0) {
      const scores = interactionResults.map(result => {
        if (result.correct !== undefined) {
          return (result.correct / result.total) * 100
        }
        return result.score || 80
      })
      finalScore = Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
    }

    const learningResults: LearningResults = {
      topicId: topic.id,
      timeSpent,
      stepsCompleted: completedSteps,
      interactionResults,
      finalScore,
      completed: true
    }

    // Submit results to duolingo service
    await duolingoLearningService.submitTopicResults(topic.id, learningResults)

    // Show celebration
    setShowCelebration(true)

    // Complete after animation
    setTimeout(() => {
      onComplete(learningResults)
    }, 2000)
  }, [startTime, completedSteps, interactionResults, topic.id, onComplete])

  const renderCurrentComponent = () => {
    if (!currentStep) return null

    const currentComponent = currentStep.components[currentStep.currentIndex]

    switch (currentStep.type) {
      case 'didactic_snippet':
        console.log('Raw didactic snippet content:', currentComponent.content)
        return (
          <DidacticSnippet
            content={currentComponent.content}
            onContinue={() => handleStepComplete('didactic')}
            isLoading={isLoading}
          />
        )

      case 'multiple_choice_question':
        // Transform the content to match MultipleChoice component interface
        const mcContent = currentComponent.content
        console.log('Raw multiple choice content:', mcContent)

        // Ensure the content has the right structure
        const transformedQuestion = {
          id: mcContent.id || `mc-${Date.now()}`,
          question: mcContent.question || mcContent.title || 'Question',
          options: Array.isArray(mcContent.options) ? mcContent.options.map((opt: any, index: number) => ({
            id: opt.id || `option-${index}`,
            text: opt.text || opt.option || opt,
            is_correct: opt.is_correct || opt.correct || false,
            explanation: opt.explanation || ''
          })) : [],
          explanation: mcContent.explanation || '',
          hint: mcContent.hint || ''
        }

        console.log('Transformed multiple choice question:', transformedQuestion)

        // Safety check
        if (!transformedQuestion.options || transformedQuestion.options.length === 0) {
          console.error('No valid options found for multiple choice question:', mcContent)
          return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
              <div className="text-center max-w-md">
                <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Content Error</h2>
                <p className="text-gray-600 mb-4">This question doesn't have valid options to display.</p>
                <button
                  onClick={() => handleStepComplete('multiple_choice', { correct: 0, total: 1 })}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Skip Question
                </button>
              </div>
            </div>
          )
        }

        return (
          <MultipleChoice
            questions={[transformedQuestion]}
            onComplete={(results) => handleStepComplete('multiple_choice', results)}
            isLoading={isLoading}
          />
        )

      case 'short_answer_question':
        // Transform the content to match ShortAnswer component interface
        const saContent = currentComponent.content
        console.log('Raw short answer content:', saContent)

        const transformedSAQuestion = {
          id: saContent.id || `sa-${Date.now()}`,
          question: saContent.question || saContent.title || 'Question',
          context: saContent.context || '',
          sample_answers: Array.isArray(saContent.sample_answers) ? saContent.sample_answers :
                         Array.isArray(saContent.answers) ? saContent.answers :
                         ['Sample answer'],
          key_concepts: Array.isArray(saContent.key_concepts) ? saContent.key_concepts :
                       Array.isArray(saContent.concepts) ? saContent.concepts :
                       [],
          evaluation_criteria: Array.isArray(saContent.evaluation_criteria) ? saContent.evaluation_criteria :
                              Array.isArray(saContent.criteria) ? saContent.criteria :
                              ['Demonstrates understanding of the concept'],
          hint: saContent.hint || ''
        }

        console.log('Transformed short answer question:', transformedSAQuestion)

        return (
          <ShortAnswer
            questions={[transformedSAQuestion]}
            onComplete={(results) => handleStepComplete('short_answer', results)}
            isLoading={isLoading}
          />
        )

      case 'socratic_dialogue':
        console.log('Raw socratic dialogue content:', currentComponent.content)
        return (
          <SocraticDialogue
            content={currentComponent.content}
            onComplete={(insights) => handleStepComplete('socratic', { insights })}
            isLoading={isLoading}
          />
        )

      case 'post_topic_quiz':
        console.log('Raw post topic quiz content:', currentComponent.content)
        return (
          <PostTopicQuiz
            quizData={currentComponent.content}
            onComplete={(results) => handleStepComplete('quiz', results)}
            onRetry={() => {}} // No retry in Duolingo mode
          />
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50">
      {/* Header with progress */}
      <div className="sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            <div className="flex-1 mx-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="flex items-center gap-1 text-orange-600">
                  <Flame className="w-4 h-4" />
                  <span className="text-sm font-medium">{streakCount}</span>
                </div>
                <div className="text-xs text-gray-500">
                  Step {currentStepIndex + 1} of {totalSteps}
                </div>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-green-600">
                <Target className="w-3 h-3 mr-1" />
                {Math.round(progress)}%
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <AnimatePresence mode="wait">
          {currentStep && (
            <motion.div
              key={`${currentStep.type}-${currentStepIndex}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderCurrentComponent()}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Celebration overlay */}
      <AnimatePresence>
        {showCelebration && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm"
          >
            <Card className="p-8 text-center max-w-sm mx-4">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: 2 }}
              >
                <Trophy className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
              </motion.div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Great job!</h3>
              <p className="text-gray-600 mb-4">
                {currentStepIndex === componentSteps.length - 1
                  ? `You completed "${topic.title}"!`
                  : "Keep it up!"
                }
              </p>
              <div className="flex items-center justify-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <Star className="w-5 h-5 text-yellow-400 fill-current" />
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mini progress indicator for steps */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40">
        <Card className="px-4 py-2 bg-white/90 backdrop-blur-sm border shadow-lg">
          <div className="flex items-center gap-2">
            {componentSteps.map((step, index) => (
              <div
                key={step.type}
                className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  index < currentStepIndex
                    ? 'bg-green-500'
                    : index === currentStepIndex
                    ? 'bg-blue-500 scale-125'
                    : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}