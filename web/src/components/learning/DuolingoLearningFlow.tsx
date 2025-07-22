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
import MultipleChoice from './MultipleChoice'
// TODO: Re-add other imports when we expand beyond MCQs

import { duolingoLearningService } from '@/services/learning/learning-flow'
import type { BiteSizedTopicDetail, ComponentType, LearningResults } from '@/types'

interface DuolingoLearningFlowProps {
  topic: BiteSizedTopicDetail
  onComplete: (results: LearningResults) => void
  onBack: () => void
}

// Simplified flow: didactic snippet then individual MCQs
const COMPONENT_ORDER: ComponentType[] = [
  'didactic_snippet',  // 1. Learn the concept
  'mcq'               // 2. Individual MCQ questions
]

interface ComponentStep {
  type: ComponentType
  components: any[]
  currentIndex: number
  isCompleted: boolean
}

export default function DuolingoLearningFlow({ topic, onComplete, onBack }: DuolingoLearningFlowProps) {
  console.log('🎯 [DuolingoLearningFlow] Component mounted with topic:', topic?.title)
  console.log('🎯 [DuolingoLearningFlow] Topic components count:', topic?.components?.length)

  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [startTime] = useState(Date.now())
  const [completedSteps, setCompletedSteps] = useState<string[]>([])
  const [interactionResults, setInteractionResults] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [streakCount, setStreakCount] = useState(0)
  const [showCelebration, setShowCelebration] = useState(false)

  // Organize components into individual steps (each MCQ gets its own step)
  const componentSteps = useMemo((): ComponentStep[] => {
    console.log('🔧 [DuolingoLearningFlow] Organizing components:', topic.components)
    console.log('🔧 [DuolingoLearningFlow] Backend component types:', topic.components.map(c => c.component_type))
    const steps: ComponentStep[] = []

    // Add didactic snippet first (if available)
    const didacticComponents = topic.components.filter(c => c.component_type === 'didactic_snippet')
    console.log(`🔍 [DuolingoLearningFlow] Looking for didactic snippets in ${topic.components.length} components`)
    console.log(`🔍 [DuolingoLearningFlow] Component types found:`, topic.components.map(c => c.component_type))
    console.log(`🔍 [DuolingoLearningFlow] Didactic components found:`, didacticComponents.length)

    if (didacticComponents.length > 0) {
      console.log(`✅ [DuolingoLearningFlow] Adding ${didacticComponents.length} didactic snippet(s) to steps`)
      steps.push({
        type: 'didactic_snippet',
        components: didacticComponents,
        currentIndex: 0,
        isCompleted: false
      })
    } else {
      console.log(`⚠️ [DuolingoLearningFlow] No didactic snippets found, starting with MCQs`)
    }

    // Add each MCQ as an individual step
    const mcqComponents = topic.components.filter(c => c.component_type === 'mcq')
    console.log(`🔧 [DuolingoLearningFlow] Found ${mcqComponents.length} MCQ components`)
    mcqComponents.forEach((mcqComponent, index) => {
      steps.push({
        type: 'mcq',
        components: [mcqComponent], // Single MCQ per step
        currentIndex: 0,
        isCompleted: false
      })
    })

    console.log('🔧 [DuolingoLearningFlow] Created steps:', steps.map(s => ({ type: s.type, componentCount: s.components.length })))
    return steps
  }, [topic.components])

  const currentStep = componentSteps[currentStepIndex]
  const totalSteps = componentSteps.length
  const progress = totalSteps > 0 ? (currentStepIndex / totalSteps) * 100 : 0

  console.log('🔧 [DuolingoLearningFlow] Current step:', currentStep)
  console.log('🔧 [DuolingoLearningFlow] Current step index:', currentStepIndex)
  console.log('🔧 [DuolingoLearningFlow] Total steps:', totalSteps)

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
    console.log('🎨 [DuolingoLearningFlow] renderCurrentComponent called')
    console.log('🎨 [DuolingoLearningFlow] currentStep:', currentStep)

    if (!currentStep) {
      console.log('❌ [DuolingoLearningFlow] No current step available!')
      return <div className="text-center p-8">
        <p className="text-red-600">No learning steps available</p>
        <p className="text-sm text-gray-600 mt-2">Debug: currentStep is {currentStep}</p>
      </div>
    }

    const currentComponent = currentStep.components[currentStep.currentIndex]
    console.log('🎨 [DuolingoLearningFlow] Current component:', currentComponent)

    switch (currentStep.type) {
      case 'didactic_snippet':
        console.log('Raw didactic snippet content:', currentComponent.content)
        return (
          <DidacticSnippet
            snippet={currentComponent.content}
            onContinue={() => handleStepComplete('didactic')}
            isLoading={isLoading}
          />
        )

      case 'mcq':
        // Transform single MCQ component (since each step now has only one MCQ)
        console.log(`🔍 [MCQ Debug] Processing single MCQ component`)

        const mcContent = currentComponent.content
        console.log(`🔍 [MCQ Debug] MCQ content:`, JSON.stringify(mcContent, null, 2))

        // Transform backend MCQ format to component format
        const mcqData = mcContent.mcq || mcContent;

        // Convert options array to choices object with A/B/C/D keys
        const choices: Record<string, string> = {};
        if (Array.isArray(mcqData.options)) {
          mcqData.options.forEach((option: string, optIndex: number) => {
            const letter = String.fromCharCode(65 + optIndex); // A, B, C, D
            choices[letter] = option;
          });
        }

        // Find correct answer key using the index
        const correctAnswerKey = mcqData.correct_answer_index !== undefined
          ? String.fromCharCode(65 + mcqData.correct_answer_index)
          : 'A';

        const transformedQuestion = {
          type: 'multiple_choice_question' as const,
          number: 1,
          title: mcqData.stem || 'Question',
          question: mcqData.stem || 'Question',
          choices: choices,
          correct_answer: correctAnswerKey,
          justifications: mcqData.justifications || {},
          target_concept: mcContent.learning_objective || '',
          purpose: 'Test understanding',
          difficulty: 2,
          tags: mcqData.rationale || ''
        }

        console.log(`🔍 [MCQ Debug] Transformed question:`, JSON.stringify(transformedQuestion, null, 2))

        // Safety check
        if (!transformedQuestion.choices || Object.keys(transformedQuestion.choices).length === 0) {
          console.error('No valid choices found for MCQ:', mcContent)
          return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
              <div className="text-center max-w-md">
                <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Content Error</h2>
                <p className="text-gray-600 mb-4">This question doesn't have valid options to display.</p>
                <button
                  onClick={() => handleStepComplete('mcq', { correct: 0, total: 1 })}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Skip Question
                </button>
              </div>
            </div>
          )
        }

        // Create quiz structure with single question
        const quiz = { questions: [transformedQuestion] };
        console.log('🎯 [MCQ Debug] Final single question quiz:', JSON.stringify(quiz, null, 2))

        return (
          <MultipleChoice
            quiz={quiz}
            onComplete={(results) => handleStepComplete('mcq', results)}
            isLoading={isLoading}
          />
        )

      // TODO: Add back other component types later

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