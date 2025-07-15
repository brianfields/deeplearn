/**
 * Generic Learning Component Renderer
 *
 * This component demonstrates how the typed component system enables
 * safe, generic handling of all learning component types.
 */

import React from 'react'
import type {
  TypedTopicComponent,
  ComponentType as NewComponentType,
  OnComponentComplete,
} from '@/types'
import {
  isDidacticSnippetContent,
  isMultipleChoiceContent,
  isSocraticDialogueContent,
  isShortAnswerContent,
  isPostTopicQuizContent,
  isGlossaryContent,
} from '@/types'

// Import all learning components
import DidacticSnippet from './DidacticSnippet'
import MultipleChoice from './MultipleChoice'
import SocraticDialogue from './SocraticDialogue'
import ShortAnswer from './ShortAnswer'
import PostTopicQuiz from './PostTopicQuiz'

interface ComponentRendererProps {
  component: TypedTopicComponent
  onComplete: OnComponentComplete
  isLoading?: boolean
  onError?: (error: string) => void
}

/**
 * Safely renders any learning component based on its type
 * with full type safety and proper prop mapping
 */
export default function ComponentRenderer({
  component,
  onComplete,
  isLoading = false,
  onError
}: ComponentRendererProps) {
  const { component_type, content } = component

  // Handle error callback wrapper
  const handleError = (error: string) => {
    console.error(`Error in ${component_type} component:`, error)
    onError?.(error)
  }

  try {
    switch (component_type) {
      case 'didactic_snippet': {
        if (!isDidacticSnippetContent(content)) {
          throw new Error('Invalid content for didactic snippet')
        }

        return (
          <DidacticSnippet
            snippet={content}
            onContinue={() => onComplete({
              componentType: component_type,
              timeSpent: 0, // Would be tracked in component
              completed: true,
              data: { completed: true }
            })}
            isLoading={isLoading}
          />
        )
      }

      case 'multiple_choice_question': {
        if (!isMultipleChoiceContent(content)) {
          throw new Error('Invalid content for multiple choice')
        }

        return (
          <MultipleChoice
            quiz={content}
            onComplete={(results) => onComplete({
              componentType: component_type,
              timeSpent: 0, // Would be tracked in component
              completed: true,
              data: results
            })}
            isLoading={isLoading}
          />
        )
      }

      case 'socratic_dialogue': {
        if (!isSocraticDialogueContent(content)) {
          throw new Error('Invalid content for socratic dialogue')
        }

        return (
          <SocraticDialogue
            dialogue={content}
            onComplete={(insights) => onComplete({
              componentType: component_type,
              timeSpent: 0, // Would be tracked in component
              completed: true,
              data: { insights }
            })}
            isLoading={isLoading}
          />
        )
      }

      case 'short_answer_question': {
        if (!isShortAnswerContent(content)) {
          throw new Error('Invalid content for short answer')
        }

        return (
          <ShortAnswer
            assessment={content}
            onComplete={(results) => onComplete({
              componentType: component_type,
              timeSpent: 0, // Would be tracked in component
              completed: true,
              data: results
            })}
            isLoading={isLoading}
          />
        )
      }

      case 'post_topic_quiz': {
        if (!isPostTopicQuizContent(content)) {
          throw new Error('Invalid content for post topic quiz')
        }

        // Pass backend data structure directly
        const quizData = {
          title: 'Post-Topic Quiz',
          description: 'Test your understanding of the topic',
          items: content.items,
          passing_score: 70,
          time_limit: 1200 // 20 minutes default
        }

        return (
          <PostTopicQuiz
            quiz={content}
            onComplete={(results) => onComplete({
              componentType: component_type,
              timeSpent: results.timeSpent,
              completed: results.passed,
              data: results
            })}
          />
        )
      }

      case 'glossary': {
        if (!isGlossaryContent(content)) {
          throw new Error('Invalid content for glossary')
        }

        // Note: Glossary component doesn't exist yet, but the type system
        // ensures we know exactly what props it needs when we create it
        return (
          <div className="p-4 text-center bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800">
              Glossary component coming soon!
            </p>
            <p className="text-sm text-yellow-600 mt-2">
              {content.entries.length} glossary entries available
            </p>
            <button
              onClick={() => onComplete({
                componentType: component_type,
                timeSpent: 0,
                completed: true,
                data: { entriesViewed: [], interactionsCount: 0 }
              })}
              className="mt-2 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
            >
              Skip for now
            </button>
          </div>
        )
      }

      default: {
        // TypeScript will catch this at compile time if we forget a case
        const exhaustiveCheck: never = component_type
        throw new Error(`Unknown component type: ${exhaustiveCheck}`)
      }
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    handleError(errorMessage)

    return (
      <div className="p-4 text-center bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800 mb-2">
          Error rendering component: {errorMessage}
        </p>
        <button
          onClick={() => onComplete({
            componentType: component_type,
            timeSpent: 0,
            completed: false,
            data: { error: errorMessage }
          })}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Skip this component
        </button>
      </div>
    )
  }
}

/**
 * Hook for managing a sequence of learning components
 */
export function useComponentSequence(components: TypedTopicComponent[]) {
  const [currentIndex, setCurrentIndex] = React.useState(0)
  const [results, setResults] = React.useState<any[]>([])
  const [isComplete, setIsComplete] = React.useState(false)

  const currentComponent = components[currentIndex]
  const isLastComponent = currentIndex === components.length - 1

  const handleComponentComplete = React.useCallback((result: any) => {
    setResults(prev => [...prev, result])

    if (isLastComponent) {
      setIsComplete(true)
    } else {
      setCurrentIndex(prev => prev + 1)
    }
  }, [isLastComponent])

  const reset = React.useCallback(() => {
    setCurrentIndex(0)
    setResults([])
    setIsComplete(false)
  }, [])

  return {
    currentComponent,
    currentIndex,
    totalComponents: components.length,
    results,
    isComplete,
    progress: ((currentIndex + (isComplete ? 1 : 0)) / components.length) * 100,
    handleComponentComplete,
    reset
  }
}

/**
 * Utility for creating type-safe component definitions
 */
export function createTypedComponent<T extends NewComponentType>(
  type: T,
  content: TypedTopicComponent<T>['content'],
  metadata: TypedTopicComponent<T>['metadata']
): TypedTopicComponent<T> {
  return {
    component_type: type,
    content,
    metadata
  } as TypedTopicComponent<T>
}

/**
 * Example usage of the typed system
 */
export const exampleComponents: TypedTopicComponent[] = [
  createTypedComponent('didactic_snippet', {
    title: 'Introduction to React',
    snippet: 'React is a library for building user interfaces...',
    type: 'didactic_snippet' as const,
    difficulty: 2,
    core_concept: 'Component-based architecture',
    key_points: ['Components are reusable', 'Props pass data down'],
    learning_objectives: ['Understand components', 'Learn about props'],
    estimated_duration: 5
  }, {
    order: 1,
    estimated_duration: 5,
    difficulty: 'beginner',
    required: true
  }),

  createTypedComponent('multiple_choice_question', {
    questions: [{
      type: 'multiple_choice_question' as const,
      number: 1,
      title: 'React Basics',
      question: 'What is React?',
      choices: {
        'A': 'A JavaScript library',
        'B': 'A programming language',
        'C': 'A database',
        'D': 'An operating system'
      },
      correct_answer: 'A',
      justifications: {
        'A': 'Correct! React is a JavaScript library for building user interfaces.',
        'B': 'Incorrect. React is not a programming language, it\'s a library.',
        'C': 'Incorrect. React is not a database.',
        'D': 'Incorrect. React is not an operating system.'
      },
      target_concept: 'React fundamentals',
      difficulty: 2,
      tags: 'Think about what React is used for in web development'
    }]
  }, {
    order: 2,
    estimated_duration: 3,
    difficulty: 'beginner',
    required: true
  })
]