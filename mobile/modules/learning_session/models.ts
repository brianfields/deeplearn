/**
 * Learning Session Models
 *
 * DTOs and types for learning session management, progress tracking, and session orchestration.
 * Designed to work with future backend/modules/learning_session/ module.
 */

// ================================
// Backend API Wire Types (Private)
// ================================

interface ApiLearningSession {
  id: string;
  lesson_id: string;
  user_id?: string;
  status: 'active' | 'completed' | 'paused' | 'abandoned';
  started_at: string;
  completed_at?: string;
  current_exercise_index: number;
  total_exercises: number;
  progress_percentage: number;
  session_data: Record<string, any>;
}

interface ApiSessionProgress {
  session_id: string;
  exercise_id: string;
  exercise_type: string;
  started_at: string;
  completed_at?: string;
  is_correct?: boolean;
  user_answer?: any;
  time_spent_seconds: number;
  attempts: number;
}

interface ApiSessionResults {
  session_id: string;
  lesson_id: string;
  total_exercises: number;
  completed_exercises: number;
  correct_exercises: number;
  total_time_seconds: number;
  completion_percentage: number;
  score_percentage: number;
  achievements: string[];
}

// ================================
// Frontend DTOs (Public)
// ================================

export interface LearningSession {
  readonly id: string;
  readonly lessonId: string;
  readonly lessonTitle?: string; // Lesson title for display
  readonly userId?: string;
  readonly status: 'active' | 'completed' | 'paused' | 'abandoned';
  readonly startedAt: string;
  readonly completedAt?: string;
  readonly currentExerciseIndex: number;
  readonly totalExercises: number;
  readonly progressPercentage: number;
  readonly sessionData: Record<string, any>;
  readonly estimatedTimeRemaining: number; // Calculated
  readonly isCompleted: boolean; // Calculated
  readonly canResume: boolean; // Calculated
}

export interface SessionProgress {
  readonly sessionId: string;
  readonly exerciseId: string;
  readonly exerciseType: 'mcq' | 'short_answer' | 'coding';
  readonly startedAt: string;
  readonly completedAt?: string;
  readonly isCorrect?: boolean;
  readonly userAnswer?: any;
  readonly timeSpentSeconds: number;
  readonly attempts: number;
  readonly isCompleted: boolean; // Calculated
  readonly accuracy: number; // Calculated (0-1)
}

export interface SessionResults {
  readonly sessionId: string;
  readonly lessonId: string;
  readonly totalExercises: number;
  readonly completedExercises: number;
  readonly correctExercises: number;
  readonly totalTimeSeconds: number;
  readonly completionPercentage: number;
  readonly scorePercentage: number;
  readonly achievements: string[];
  readonly grade: 'A' | 'B' | 'C' | 'D' | 'F'; // Calculated
  readonly timeDisplay: string; // Formatted time
  readonly performanceSummary: string; // Calculated summary
}

export interface ExerciseState {
  readonly id: string;
  readonly type: 'mcq' | 'short_answer' | 'coding';
  readonly title: string;
  readonly content: any;
  readonly isCompleted: boolean;
  readonly isCorrect?: boolean;
  readonly userAnswer?: any;
  readonly attempts: number;
  readonly timeSpent: number;
  readonly maxAttempts?: number;
}

// ================================
// Request/Response Types
// ================================

export interface StartSessionRequest {
  lessonId: string;
  userId?: string;
}

export interface UpdateProgressRequest {
  sessionId: string;
  exerciseId: string;
  exerciseType: 'mcq' | 'short_answer' | 'coding';
  userAnswer?: any;
  isCorrect?: boolean;
  timeSpentSeconds: number;
}

export interface CompleteSessionRequest {
  sessionId: string;
}

// ================================
// Client State Types
// ================================

export interface SessionFilters {
  status?: 'active' | 'completed' | 'paused' | 'abandoned';
  lessonId?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface SessionUIState {
  currentExerciseIndex: number;
  showResults: boolean;
  showProgress: boolean;
  isFullscreen: boolean;
  autoAdvance: boolean;
  soundEnabled: boolean;
}

// ================================
// Error Types
// ================================

export interface LearningSessionError {
  code: 'LEARNING_SESSION_ERROR';
  message: string;
  details?: any;
}

// ================================
// DTO Conversion Functions
// ================================

/**
 * Convert API LearningSession to frontend DTO
 */
export function toLearningSessionDTO(
  api: ApiLearningSession,
  lessonTitle?: string
): LearningSession {
  const isCompleted = api.status === 'completed';
  const canResume = api.status === 'active' || api.status === 'paused';

  // Estimate 3 minutes per remaining exercise
  const remainingExercises = Math.max(
    0,
    api.total_exercises - api.current_exercise_index
  );
  const estimatedTimeRemaining = remainingExercises * 3 * 60; // seconds

  return {
    id: api.id,
    lessonId: api.lesson_id,
    lessonTitle,
    userId: api.user_id,
    status: api.status,
    startedAt: api.started_at,
    completedAt: api.completed_at,
    currentExerciseIndex: api.current_exercise_index,
    totalExercises: api.total_exercises,
    progressPercentage: api.progress_percentage,
    sessionData: api.session_data,
    estimatedTimeRemaining,
    isCompleted,
    canResume,
  };
}

/**
 * Convert API SessionProgress to frontend DTO
 */
export function toSessionProgressDTO(api: ApiSessionProgress): SessionProgress {
  const isCompleted = !!api.completed_at;
  const accuracy = api.is_correct !== undefined ? (api.is_correct ? 1 : 0) : 0;

  return {
    sessionId: api.session_id,
    exerciseId: api.exercise_id,
    exerciseType: api.exercise_type as 'mcq' | 'short_answer' | 'coding',
    startedAt: api.started_at,
    completedAt: api.completed_at,
    isCorrect: api.is_correct,
    userAnswer: api.user_answer,
    timeSpentSeconds: api.time_spent_seconds,
    attempts: api.attempts,
    isCompleted,
    accuracy,
  };
}

/**
 * Convert API SessionResults to frontend DTO
 */
export function toSessionResultsDTO(api: ApiSessionResults): SessionResults {
  const grade = calculateGrade(api.score_percentage);
  const timeDisplay = formatTime(api.total_time_seconds);
  const performanceSummary = generatePerformanceSummary(
    api.completion_percentage,
    api.score_percentage,
    api.total_time_seconds
  );

  return {
    sessionId: api.session_id,
    lessonId: api.lesson_id,
    totalExercises: api.total_exercises,
    completedExercises: api.completed_exercises,
    correctExercises: api.correct_exercises,
    totalTimeSeconds: api.total_time_seconds,
    completionPercentage: api.completion_percentage,
    scorePercentage: api.score_percentage,
    achievements: api.achievements,
    grade,
    timeDisplay,
    performanceSummary,
  };
}

// ================================
// Helper Functions
// ================================

function calculateGrade(scorePercentage: number): 'A' | 'B' | 'C' | 'D' | 'F' {
  if (scorePercentage >= 90) return 'A';
  if (scorePercentage >= 80) return 'B';
  if (scorePercentage >= 70) return 'C';
  if (scorePercentage >= 60) return 'D';
  return 'F';
}

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }

  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

function generatePerformanceSummary(
  completionPercentage: number,
  scorePercentage: number,
  totalTimeSeconds: number
): string {
  const timeMinutes = Math.round(totalTimeSeconds / 60);

  if (completionPercentage === 100 && scorePercentage >= 90) {
    return `Excellent work! Completed in ${timeMinutes} minutes with ${scorePercentage}% accuracy.`;
  }

  if (completionPercentage === 100 && scorePercentage >= 70) {
    return `Good job! Completed in ${timeMinutes} minutes with ${scorePercentage}% accuracy.`;
  }

  if (completionPercentage >= 80) {
    return `Making progress! ${completionPercentage}% complete with ${scorePercentage}% accuracy.`;
  }

  return `Keep going! ${completionPercentage}% complete. You're learning!`;
}
