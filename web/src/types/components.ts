/**
 * TypeScript types for bite-sized learning components
 *
 * This file defines specific types for each component type to ensure
 * type safety and consistent interfaces across all learning components.
 */

// ================================
// Base Component Types
// ================================

/**
 * Common props shared by all learning components
 */
export interface BaseLearningComponentProps {
  isLoading?: boolean
  onError?: (error: string) => void
}

/**
 * Results returned from component interactions
 */
export interface ComponentResults {
  componentType: ComponentType
  timeSpent: number
  completed: boolean
  data: any // Specific to each component type
}

/**
 * Common callback for component completion
 */
export type OnComponentComplete = (results: ComponentResults) => void

// ================================
// Didactic Snippet Types
// ================================

export interface DidacticSnippetContent {
  title: string
  snippet: string  // Backend returns 'snippet', not 'main_content'
  type: 'didactic_snippet'
  difficulty: number
  // Optional fields that may be added by generation metadata
  core_concept?: string
  key_points?: string[]
  learning_objectives?: string[]
  estimated_duration?: number
}

export interface DidacticSnippetProps extends BaseLearningComponentProps {
  snippet: DidacticSnippetContent
  onContinue: () => void
}

export interface DidacticSnippetResults {
  timeSpent: number
  completed: boolean
}

// ================================
// Multiple Choice Types
// ================================

export interface MultipleChoiceQuestion {
  type: 'multiple_choice_question'
  number: number
  title: string
  question: string
  choices: Record<string, string>  // Backend returns as object like {A: "text", B: "text"}
  correct_answer: string
  justifications?: Record<string, string>  // Optional justifications for each choice
  target_concept?: string
  purpose?: string
  difficulty: number
  tags?: string
}

export interface MultipleChoiceContent {
  questions: MultipleChoiceQuestion[]
}

export interface MultipleChoiceProps extends BaseLearningComponentProps {
  quiz: MultipleChoiceContent
  onComplete: OnComponentComplete
}

export interface MultipleChoiceResults {
  correct: number
  total: number
  timeSpent: number
  details: Array<{
    questionId: string
    question: string
    selectedOption: string
    selectedText: string
    isCorrect: boolean
    explanation?: string
  }>
}

// ================================
// Socratic Dialogue Types
// ================================

export interface SocraticDialogueContent {
  type: 'socratic_dialogue'
  number: number
  title: string
  concept: string
  dialogue_objective: string
  starting_prompt: string  // Backend calls this 'starting_prompt', not 'initial_question'
  dialogue_style: string
  hints_and_scaffolding: string
  exit_criteria: string
  difficulty: number
  tags?: string
}

export interface SocraticDialogueProps extends BaseLearningComponentProps {
  dialogue: SocraticDialogueContent
  onComplete: OnComponentComplete
}

export interface SocraticDialogueResults {
  insights: string[]
  messageCount: number
  timeSpent: number
  completed: boolean
}

// ================================
// Short Answer Types
// ================================

export interface ShortAnswerQuestion {
  type: 'short_answer_question'
  number: number
  title: string
  question: string
  purpose: string
  target_concept: string
  expected_elements: string  // Backend returns as string, not array
  difficulty: number
  tags?: string
}

export interface ShortAnswerContent {
  questions: ShortAnswerQuestion[]
}

export interface ShortAnswerProps extends BaseLearningComponentProps {
  assessment: ShortAnswerContent
  onComplete: OnComponentComplete
}

export interface ShortAnswerResults {
  responses: Array<{
    questionId: string
    question: string
    answer: string
    feedback: {
      type: 'excellent' | 'good' | 'needs_improvement' | 'incomplete'
      score: number
      strengths: string[]
      improvements: string[]
      keyConceptsCovered: string[]
      overallComment: string
    }
  }>
  timeSpent: number
  averageScore: number
}

// ================================
// Post Topic Quiz Types
// ================================

export interface BaseQuizItem {
  title: string
  type: string  // Backend returns various types like "Multiple Choice", "Short Answer", etc.
  question: string
  target_concept: string
  difficulty: number
  tags?: string
}

export interface MultipleChoiceQuizItem extends BaseQuizItem {
  type: 'Multiple Choice'
  choices: Record<string, string>
  correct_answer: string
  justifications?: Record<string, string>
}

export interface ShortAnswerQuizItem extends BaseQuizItem {
  type: 'Short Answer'
  expected_elements: string
}

export interface DialogueQuizItem extends BaseQuizItem {
  type: 'Assessment Dialogue'
  dialogue_objective: string
  scaffolding_prompts: string
  exit_criteria: string
}

export type QuizItem = MultipleChoiceQuizItem | ShortAnswerQuizItem | DialogueQuizItem

export interface PostTopicQuizContent {
  items: QuizItem[]  // Backend returns mixed format items
}

export interface PostTopicQuizProps extends BaseLearningComponentProps {
  quiz: PostTopicQuizContent
  onComplete: OnComponentComplete
  onRetry?: () => void
}

export interface PostTopicQuizResults {
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
  answers: Array<{
    questionId: string
    question: string
    userAnswer: string
    correctAnswer: string | string[]
    isCorrect: boolean
    difficulty: 'easy' | 'medium' | 'hard'
    points: number
    explanation: string
  }>
}

// ================================
// Glossary Types
// ================================

export interface GlossaryEntry {
  type: 'glossary_entry'
  number: number
  concept: string
  title: string
  explanation: string
  difficulty: number
}

export interface GlossaryContent {
  entries: GlossaryEntry[]  // Backend returns array of entries directly
}

export interface GlossaryProps extends BaseLearningComponentProps {
  glossary: GlossaryContent
  onComplete: OnComponentComplete
}

export interface GlossaryResults {
  entriesViewed: string[]  // Changed from termsViewed to entriesViewed
  timeSpent: number
  interactionsCount: number
  completed: boolean
}

// ================================
// Union Types for Generic Handling
// ================================

/**
 * Content types for all components
 */
export type ComponentContent =
  | DidacticSnippetContent
  | MultipleChoiceContent
  | SocraticDialogueContent
  | ShortAnswerContent
  | PostTopicQuizContent
  | GlossaryContent

/**
 * Props for all components
 */
export type ComponentProps =
  | DidacticSnippetProps
  | MultipleChoiceProps
  | SocraticDialogueProps
  | ShortAnswerProps
  | PostTopicQuizProps
  | GlossaryProps

/**
 * Results from all components
 */
export type ComponentResultsData =
  | DidacticSnippetResults
  | MultipleChoiceResults
  | SocraticDialogueResults
  | ShortAnswerResults
  | PostTopicQuizResults
  | GlossaryResults

/**
 * Component type discriminator
 */
export type ComponentType =
  | 'didactic_snippet'
  | 'multiple_choice_question'
  | 'mcq'  // Backend uses 'mcq' for multiple choice questions
  | 'socratic_dialogue'
  | 'short_answer_question'
  | 'post_topic_quiz'
  | 'glossary'

// ================================
// Type Guards
// ================================

export function isDidacticSnippetContent(content: ComponentContent): content is DidacticSnippetContent {
  return 'snippet' in content && 'title' in content && (content as any).type === 'didactic_snippet'
}

export function isMultipleChoiceContent(content: ComponentContent): content is MultipleChoiceContent {
  return 'questions' in content && Array.isArray((content as any).questions) &&
         (content as any).questions[0]?.type === 'multiple_choice_question'
}

export function isSocraticDialogueContent(content: ComponentContent): content is SocraticDialogueContent {
  return 'starting_prompt' in content && 'concept' in content && (content as any).type === 'socratic_dialogue'
}

export function isShortAnswerContent(content: ComponentContent): content is ShortAnswerContent {
  return 'questions' in content && Array.isArray((content as any).questions) &&
         (content as any).questions[0]?.type === 'short_answer_question'
}

export function isPostTopicQuizContent(content: ComponentContent): content is PostTopicQuizContent {
  return 'items' in content && Array.isArray((content as any).items)
}

export function isGlossaryContent(content: ComponentContent): content is GlossaryContent {
  return 'entries' in content && Array.isArray((content as any).entries) &&
         (content as any).entries[0]?.type === 'glossary_entry'
}

// ================================
// Enhanced TopicComponent Interface
// ================================

/**
 * Enhanced version of TopicComponent with proper typing
 */
export interface TypedTopicComponent<T extends ComponentType = ComponentType> {
  component_type: T
  content: T extends 'didactic_snippet' ? DidacticSnippetContent :
           T extends 'multiple_choice_question' ? MultipleChoiceContent :
           T extends 'socratic_dialogue' ? SocraticDialogueContent :
           T extends 'short_answer_question' ? ShortAnswerContent :
           T extends 'post_topic_quiz' ? PostTopicQuizContent :
           T extends 'glossary' ? GlossaryContent :
           ComponentContent
  metadata: {
    order: number
    estimated_duration: number
    difficulty: 'beginner' | 'intermediate' | 'advanced'
    required: boolean
    [key: string]: any
  }
}