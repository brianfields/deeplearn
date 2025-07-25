/**
 * Shared types for the React Native Learning App
 *
 * These types are adapted from the web application to work with React Native
 */

// ================================
// Core Learning Types
// ================================

export type UserLevel = 'beginner' | 'intermediate' | 'advanced';
export type ComponentType =
  | 'didactic_snippet'
  | 'mcq'
  | 'short_answer'
  | 'socratic_dialogue'
  | 'post_topic_quiz';

export interface BiteSizedTopic {
  id: string;
  title: string;
  description: string;
  estimated_duration: number;
  difficulty: number;
  learning_objectives: string[];
  prerequisites: string[];
  component_count: number;
  created_at: string;
  updated_at: string;
}

export interface BiteSizedTopicDetail extends BiteSizedTopic {
  components: LearningComponent[];
}

export interface LearningComponent {
  id: string;
  component_type: ComponentType;
  content: any;
  order_index: number;
  estimated_duration: number;
  learning_objective: string;
  created_at: string;
  updated_at: string;
}

export interface LearningResults {
  topicId: string;
  timeSpent: number;
  stepsCompleted: string[];
  interactionResults: any[];
  finalScore: number;
  completed: boolean;
}

// ================================
// Component-specific Types
// ================================

export interface DidacticSnippetContent {
  title: string;
  snippet: string;
  core_concept: string;
  estimated_duration: number;
  key_points?: string[];
  examples?: string[];
}

export interface MCQContent {
  mcq: {
    stem: string;
    options: string[];
    correct_answer_index: number;
    justifications?: Record<string, string>;
    rationale?: string;
  };
  learning_objective: string;
}

export interface ShortAnswerContent {
  question: string;
  expected_elements: string;
  learning_objective: string;
  assessment_criteria: string;
}

export interface SocraticDialogueContent {
  starting_prompt: string;
  dialogue_objective: string;
  scaffolding_prompts: string;
  exit_criteria: string;
}

// ================================
// Progress & Session Types
// ================================

export interface TopicProgress {
  topicId: string;
  currentComponentIndex: number;
  completedComponents: string[];
  startTime: number;
  timeSpent: number;
  score: number;
  interactionResults: any[];
  completed: boolean;
  lastUpdated: number;
}

export interface LearningSession {
  sessionId: string;
  topicIds: string[];
  currentTopicIndex: number;
  startTime: number;
  totalTimeSpent: number;
  streak: number;
  dailyGoal: number;
  dailyProgress: number;
}

// ================================
// API Types
// ================================

export interface ApiResponse<T = unknown> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  message: string;
  code?: string;
  status: number;
  details?: unknown;
}

// ================================
// Component Props Types
// ================================

export interface DidacticSnippetProps {
  snippet: DidacticSnippetContent;
  onContinue: () => void;
  isLoading?: boolean;
}

export interface MultipleChoiceProps {
  question: MultipleChoiceQuestion;
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

// Legacy interface for quiz-based multiple choice (if needed for compatibility)
export interface MultipleChoiceQuizProps {
  quiz: {
    questions: MultipleChoiceQuestion[];
  };
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

export interface MultipleChoiceQuestion {
  title: string;
  question: string;
  choices: Record<string, string>; // Answer choices keyed by letter (A, B, C, D)
  correct_answer: string; // Letter of the correct answer
  correct_answer_index?: number; // Zero-based index of correct answer
  justifications: Record<string, string>; // Explanations for why each choice is correct/incorrect
  target_concept: string; // The key concept this question tests
  purpose: string; // Type of assessment (e.g., misconception check, concept contrast)
  type?: string; // Content type identifier, defaults to "multiple_choice_question"
  difficulty: number; // Difficulty level from 1-5
  tags?: string; // Optional tags for usage metadata
  number?: number; // Position number in the question set
  generation_metadata?: any; // Metadata about content generation
}

export interface ShortAnswerProps {
  assessment: {
    question: string;
    expected_elements: string;
    learning_objective: string;
  };
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

export interface SocraticDialogueProps {
  dialogue: SocraticDialogueContent;
  onComplete: (results: any) => void;
  isLoading?: boolean;
}

// ================================
// Navigation Types
// ================================

export type RootStackParamList = {
  Dashboard: undefined;
  Learning: { topicId: string };
  TopicDetail: { topicId: string; topic: BiteSizedTopicDetail };
};

export type LearningStackParamList = {
  TopicList: undefined;
  LearningFlow: { topicId: string; topic: BiteSizedTopicDetail };
  Results: { results: LearningResults };
};

// ================================
// Style Types
// ================================

export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

export interface Spacing {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

export interface Typography {
  heading1: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  heading2: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  heading3: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  body: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
  caption: {
    fontSize: number;
    fontWeight: string;
    lineHeight: number;
  };
}

export interface Theme {
  colors: ThemeColors;
  spacing: Spacing;
  typography: Typography;
}
