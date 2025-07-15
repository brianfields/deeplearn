// Learning Components
export { default as DidacticSnippet } from './DidacticSnippet'
export { default as DuolingoLearningFlow } from './DuolingoLearningFlow'
export { default as MultipleChoice } from './MultipleChoice'
export { default as PostTopicQuiz } from './PostTopicQuiz'
export { default as ShortAnswer } from './ShortAnswer'
export { default as SocraticDialogue } from './SocraticDialogue'

// Generic component renderer and utilities
export {
  default as ComponentRenderer,
  useComponentSequence,
  createTypedComponent,
  exampleComponents
} from './ComponentRenderer'

// Type exports for learning components (deprecated - use typed system instead)
export type { default as DidacticSnippetProps } from './DidacticSnippet'
export type { default as SocraticDialogueProps } from './SocraticDialogue'
export type { default as MultipleChoiceProps } from './MultipleChoice'
export type { default as ShortAnswerProps } from './ShortAnswer'
export type { default as PostTopicQuizProps } from './PostTopicQuiz'
