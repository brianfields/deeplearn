/**
 * Learning Session Store
 *
 * Zustand store for client-side learning session state management.
 * Handles UI state, session preferences, and temporary session data.
 */

import { create } from 'zustand';
import type { SessionUIState, ExerciseState } from './models';

interface LearningSessionState {
  // Current session UI state
  currentSessionId: string | null;
  currentUnitId: string | null;
  uiState: SessionUIState;

  // Exercise interaction state
  currentExerciseIndex: number;
  exerciseStates: Record<string, ExerciseState>; // exerciseId -> state (only actual exercises)

  // User preferences
  preferences: {
    autoAdvance: boolean;
    soundEnabled: boolean;
    showHints: boolean;
    animationsEnabled: boolean;
    fontSize: 'small' | 'medium' | 'large';
  };

  // Temporary session data (not persisted to server)
  sessionNotes: Record<string, string>; // exerciseId -> notes
  bookmarks: string[]; // exerciseIds

  // Performance tracking
  exerciseStartTimes: Record<string, number>; // exerciseId -> timestamp

  // Actions
  setCurrentSession: (sessionId: string | null, unitId?: string | null) => void;
  setCurrentUnit: (unitId: string | null) => void;
  updateUIState: (updates: Partial<SessionUIState>) => void;
  setCurrentExercise: (index: number) => void;
  updateExerciseState: (
    exerciseId: string,
    state: Partial<ExerciseState>
  ) => void;
  startExercise: (exerciseId: string) => void;
  completeExercise: (
    exerciseId: string,
    exerciseType: 'mcq' | 'short_answer' | 'coding',
    isCorrect?: boolean,
    userAnswer?: any
  ) => void;

  // Preferences
  updatePreferences: (
    updates: Partial<LearningSessionState['preferences']>
  ) => void;

  // Notes and bookmarks
  addNote: (exerciseId: string, note: string) => void;
  removeNote: (exerciseId: string) => void;
  toggleBookmark: (exerciseId: string) => void;

  // Session management
  resetSession: () => void;
  pauseSession: () => void;
  resumeSession: () => void;

  // Performance tracking
  getExerciseTimeSpent: (exerciseId: string) => number;
  getTotalTimeSpent: () => number;
}

export const useLearningSessionStore = create<LearningSessionState>(
  (set, get) => ({
    // Initial state
    currentSessionId: null,
    currentUnitId: null,
    uiState: {
      currentExerciseIndex: 0,
      showResults: false,
      showProgress: true,
      isFullscreen: false,
      autoAdvance: false,
      soundEnabled: true,
    },
    currentExerciseIndex: 0,
    exerciseStates: {},
    preferences: {
      autoAdvance: false,
      soundEnabled: true,
      showHints: true,
      animationsEnabled: true,
      fontSize: 'medium',
    },
    sessionNotes: {},
    bookmarks: [],
    exerciseStartTimes: {},

    // Actions
    setCurrentSession: (sessionId, unitId) => {
      set(state => {
        // Reset session-specific state when changing sessions
        if (state.currentSessionId !== sessionId) {
          return {
            ...state,
            currentSessionId: sessionId,
            currentUnitId: unitId ?? null,
            currentExerciseIndex: 0,
            exerciseStates: {},
            sessionNotes: {},
            bookmarks: [],
            exerciseStartTimes: {},
            uiState: {
              ...state.uiState,
              currentExerciseIndex: 0,
              showResults: false,
              isFullscreen: false,
            },
          };
        }
        const nextUnitId =
          unitId !== undefined
            ? unitId
            : sessionId === null
              ? null
              : state.currentUnitId;
        return { ...state, currentSessionId: sessionId, currentUnitId: nextUnitId };
      });
    },

    setCurrentUnit: unitId => {
      set(state => ({ ...state, currentUnitId: unitId }));
    },

    updateUIState: updates => {
      set(state => ({
        ...state,
        uiState: { ...state.uiState, ...updates },
      }));
    },

    setCurrentExercise: (index: number) => {
      set(state => ({
        ...state,
        currentExerciseIndex: index,
        uiState: { ...state.uiState, currentExerciseIndex: index },
      }));
    },

    updateExerciseState: (
      exerciseId: string,
      stateUpdates: Partial<ExerciseState>
    ) => {
      set(state => ({
        ...state,
        exerciseStates: {
          ...state.exerciseStates,
          [exerciseId]: {
            ...state.exerciseStates[exerciseId],
            ...stateUpdates,
          },
        },
      }));
    },

    startExercise: (exerciseId: string) => {
      const now = Date.now();
      set(state => ({
        ...state,
        exerciseStartTimes: {
          ...state.exerciseStartTimes,
          [exerciseId]: now,
        },
      }));
    },

    completeExercise: (
      exerciseId: string,
      exerciseType: 'mcq' | 'short_answer' | 'coding',
      isCorrect?: boolean,
      userAnswer?: any
    ) => {
      const state = get();
      const startTime = state.exerciseStartTimes[exerciseId];
      const timeSpent = startTime ? Date.now() - startTime : 0;

      set(currentState => ({
        ...currentState,
        exerciseStates: {
          ...currentState.exerciseStates,
          [exerciseId]: {
            id: exerciseId,
            type: exerciseType,
            title: currentState.exerciseStates[exerciseId]?.title || 'Exercise',
            content: currentState.exerciseStates[exerciseId]?.content || {},
            isCompleted: true,
            isCorrect,
            userAnswer,
            timeSpent: timeSpent / 1000, // Convert to seconds
            attempts:
              (currentState.exerciseStates[exerciseId]?.attempts || 0) + 1,
            maxAttempts: currentState.exerciseStates[exerciseId]?.maxAttempts,
          },
        },
      }));

      // Auto-advance if enabled
      if (state.preferences.autoAdvance) {
        const nextIndex = state.currentExerciseIndex + 1;
        get().setCurrentExercise(nextIndex);
      }
    },

    updatePreferences: updates => {
      set(state => ({
        ...state,
        preferences: { ...state.preferences, ...updates },
        uiState: {
          ...state.uiState,
          autoAdvance: updates.autoAdvance ?? state.uiState.autoAdvance,
          soundEnabled: updates.soundEnabled ?? state.uiState.soundEnabled,
        },
      }));
    },

    addNote: (exerciseId: string, note: string) => {
      set(state => ({
        ...state,
        sessionNotes: {
          ...state.sessionNotes,
          [exerciseId]: note,
        },
      }));
    },

    removeNote: (exerciseId: string) => {
      set(state => {
        const { [exerciseId]: _removed, ...remainingNotes } =
          state.sessionNotes;
        return {
          ...state,
          sessionNotes: remainingNotes,
        };
      });
    },

    toggleBookmark: (exerciseId: string) => {
      set(state => {
        const isBookmarked = state.bookmarks.includes(exerciseId);
        return {
          ...state,
          bookmarks: isBookmarked
            ? state.bookmarks.filter(id => id !== exerciseId)
            : [...state.bookmarks, exerciseId],
        };
      });
    },

    resetSession: () => {
      set(state => ({
        ...state,
        currentExerciseIndex: 0,
        exerciseStates: {},
        sessionNotes: {},
        bookmarks: [],
        exerciseStartTimes: {},
        uiState: {
          ...state.uiState,
          currentExerciseIndex: 0,
          showResults: false,
          isFullscreen: false,
        },
      }));
    },

    pauseSession: () => {
      set(state => ({
        ...state,
        uiState: { ...state.uiState, showResults: false },
      }));
    },

    resumeSession: () => {
      // Resume from current exercise
      set(state => ({
        ...state,
        uiState: { ...state.uiState, showResults: false },
      }));
    },

    getExerciseTimeSpent: (exerciseId: string) => {
      const state = get();
      const exerciseState = state.exerciseStates[exerciseId];
      if (exerciseState?.timeSpent) {
        return exerciseState.timeSpent;
      }

      // If exercise is currently active, calculate time since start
      const startTime = state.exerciseStartTimes[exerciseId];
      if (startTime) {
        return (Date.now() - startTime) / 1000; // Convert to seconds
      }

      return 0;
    },

    getTotalTimeSpent: () => {
      const state = get();
      let total = 0;

      // Add completed exercise times
      Object.values(state.exerciseStates).forEach(exerciseState => {
        if (exerciseState.timeSpent) {
          total += exerciseState.timeSpent;
        }
      });

      // Add current exercise time if active
      Object.entries(state.exerciseStartTimes).forEach(
        ([exerciseId, startTime]) => {
          if (!state.exerciseStates[exerciseId]?.isCompleted) {
            total += (Date.now() - startTime) / 1000;
          }
        }
      );

      return total;
    },
  })
);

// Selectors for common use cases
export const useLearningSessionSelectors = () => {
  const store = useLearningSessionStore();

  return {
    // Current session info
    isSessionActive: !!store.currentSessionId,
    currentSession: store.currentSessionId,
    currentExercise: store.currentExerciseIndex,

    // UI state
    isFullscreen: store.uiState.isFullscreen,
    showProgress: store.uiState.showProgress,
    autoAdvance: store.uiState.autoAdvance,

    // Progress info
    completedExercises: Object.values(store.exerciseStates).filter(
      (c: any) => c && (c as ExerciseState).isCompleted
    ).length,
    totalTimeSpent: store.getTotalTimeSpent(),

    // User preferences
    preferences: store.preferences,

    // Notes and bookmarks
    hasNotes: Object.keys(store.sessionNotes).length > 0,
    hasBookmarks: store.bookmarks.length > 0,
    noteCount: Object.keys(store.sessionNotes).length,
    bookmarkCount: store.bookmarks.length,
  };
};

// Hook for exercise-specific state
export const useExerciseState = (exerciseId: string) => {
  const store = useLearningSessionStore();

  return {
    state: store.exerciseStates[exerciseId],
    note: store.sessionNotes[exerciseId],
    isBookmarked: store.bookmarks.includes(exerciseId),
    timeSpent: store.getExerciseTimeSpent(exerciseId),

    // Actions
    updateState: (updates: Partial<ExerciseState>) =>
      store.updateExerciseState(exerciseId, updates),
    start: () => store.startExercise(exerciseId),
    complete: (isCorrect?: boolean, userAnswer?: any) => {
      const exerciseState = store.exerciseStates[exerciseId];
      if (exerciseState) {
        store.completeExercise(
          exerciseId,
          exerciseState.type,
          isCorrect,
          userAnswer
        );
      }
    },
    addNote: (note: string) => store.addNote(exerciseId, note),
    removeNote: () => store.removeNote(exerciseId),
    toggleBookmark: () => store.toggleBookmark(exerciseId),
  };
};
