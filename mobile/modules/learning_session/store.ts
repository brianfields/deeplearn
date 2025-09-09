/**
 * Learning Session Store
 *
 * Zustand store for client-side learning session state management.
 * Handles UI state, session preferences, and temporary session data.
 */

import { create } from 'zustand';
import type { SessionUIState, ComponentState } from './models';

interface LearningSessionState {
  // Current session UI state
  currentSessionId: string | null;
  uiState: SessionUIState;

  // Component interaction state
  currentComponentIndex: number;
  componentStates: Record<string, ComponentState>; // componentId -> state

  // User preferences
  preferences: {
    autoAdvance: boolean;
    soundEnabled: boolean;
    showHints: boolean;
    animationsEnabled: boolean;
    fontSize: 'small' | 'medium' | 'large';
  };

  // Temporary session data (not persisted to server)
  sessionNotes: Record<string, string>; // componentId -> notes
  bookmarks: string[]; // componentIds

  // Performance tracking
  componentStartTimes: Record<string, number>; // componentId -> timestamp

  // Actions
  setCurrentSession: (sessionId: string | null) => void;
  updateUIState: (updates: Partial<SessionUIState>) => void;
  setCurrentComponent: (index: number) => void;
  updateComponentState: (
    componentId: string,
    state: Partial<ComponentState>
  ) => void;
  startComponent: (componentId: string) => void;
  completeComponent: (
    componentId: string,
    isCorrect?: boolean,
    userAnswer?: any
  ) => void;

  // Preferences
  updatePreferences: (
    updates: Partial<LearningSessionState['preferences']>
  ) => void;

  // Notes and bookmarks
  addNote: (componentId: string, note: string) => void;
  removeNote: (componentId: string) => void;
  toggleBookmark: (componentId: string) => void;

  // Session management
  resetSession: () => void;
  pauseSession: () => void;
  resumeSession: () => void;

  // Performance tracking
  getComponentTimeSpent: (componentId: string) => number;
  getTotalTimeSpent: () => number;
}

export const useLearningSessionStore = create<LearningSessionState>(
  (set, get) => ({
    // Initial state
    currentSessionId: null,
    uiState: {
      currentComponentIndex: 0,
      showResults: false,
      showProgress: true,
      isFullscreen: false,
      autoAdvance: false,
      soundEnabled: true,
    },
    currentComponentIndex: 0,
    componentStates: {},
    preferences: {
      autoAdvance: false,
      soundEnabled: true,
      showHints: true,
      animationsEnabled: true,
      fontSize: 'medium',
    },
    sessionNotes: {},
    bookmarks: [],
    componentStartTimes: {},

    // Actions
    setCurrentSession: sessionId => {
      set(state => {
        // Reset session-specific state when changing sessions
        if (state.currentSessionId !== sessionId) {
          return {
            ...state,
            currentSessionId: sessionId,
            currentComponentIndex: 0,
            componentStates: {},
            sessionNotes: {},
            bookmarks: [],
            componentStartTimes: {},
            uiState: {
              ...state.uiState,
              currentComponentIndex: 0,
              showResults: false,
              isFullscreen: false,
            },
          };
        }
        return { ...state, currentSessionId: sessionId };
      });
    },

    updateUIState: updates => {
      set(state => ({
        ...state,
        uiState: { ...state.uiState, ...updates },
      }));
    },

    setCurrentComponent: index => {
      set(state => ({
        ...state,
        currentComponentIndex: index,
        uiState: { ...state.uiState, currentComponentIndex: index },
      }));
    },

    updateComponentState: (componentId, stateUpdates) => {
      set(state => ({
        ...state,
        componentStates: {
          ...state.componentStates,
          [componentId]: {
            ...state.componentStates[componentId],
            ...stateUpdates,
          },
        },
      }));
    },

    startComponent: componentId => {
      const now = Date.now();
      set(state => ({
        ...state,
        componentStartTimes: {
          ...state.componentStartTimes,
          [componentId]: now,
        },
      }));
    },

    completeComponent: (componentId, isCorrect, userAnswer) => {
      const state = get();
      const startTime = state.componentStartTimes[componentId];
      const timeSpent = startTime ? Date.now() - startTime : 0;

      set(currentState => ({
        ...currentState,
        componentStates: {
          ...currentState.componentStates,
          [componentId]: {
            ...currentState.componentStates[componentId],
            isCompleted: true,
            isCorrect,
            userAnswer,
            timeSpent: timeSpent / 1000, // Convert to seconds
            attempts:
              (currentState.componentStates[componentId]?.attempts || 0) + 1,
          },
        },
      }));

      // Auto-advance if enabled
      if (state.preferences.autoAdvance) {
        const nextIndex = state.currentComponentIndex + 1;
        get().setCurrentComponent(nextIndex);
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

    addNote: (componentId, note) => {
      set(state => ({
        ...state,
        sessionNotes: {
          ...state.sessionNotes,
          [componentId]: note,
        },
      }));
    },

    removeNote: componentId => {
      set(state => {
        const { [componentId]: _removed, ...remainingNotes } =
          state.sessionNotes;
        return {
          ...state,
          sessionNotes: remainingNotes,
        };
      });
    },

    toggleBookmark: componentId => {
      set(state => {
        const isBookmarked = state.bookmarks.includes(componentId);
        return {
          ...state,
          bookmarks: isBookmarked
            ? state.bookmarks.filter(id => id !== componentId)
            : [...state.bookmarks, componentId],
        };
      });
    },

    resetSession: () => {
      set(state => ({
        ...state,
        currentComponentIndex: 0,
        componentStates: {},
        sessionNotes: {},
        bookmarks: [],
        componentStartTimes: {},
        uiState: {
          ...state.uiState,
          currentComponentIndex: 0,
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
      // Resume from current component
      set(state => ({
        ...state,
        uiState: { ...state.uiState, showResults: false },
      }));
    },

    getComponentTimeSpent: componentId => {
      const state = get();
      const componentState = state.componentStates[componentId];
      if (componentState?.timeSpent) {
        return componentState.timeSpent;
      }

      // If component is currently active, calculate time since start
      const startTime = state.componentStartTimes[componentId];
      if (startTime) {
        return (Date.now() - startTime) / 1000; // Convert to seconds
      }

      return 0;
    },

    getTotalTimeSpent: () => {
      const state = get();
      let total = 0;

      // Add completed component times
      Object.values(state.componentStates).forEach(componentState => {
        if (componentState.timeSpent) {
          total += componentState.timeSpent;
        }
      });

      // Add current component time if active
      Object.entries(state.componentStartTimes).forEach(
        ([componentId, startTime]) => {
          if (!state.componentStates[componentId]?.isCompleted) {
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
    currentComponent: store.currentComponentIndex,

    // UI state
    isFullscreen: store.uiState.isFullscreen,
    showProgress: store.uiState.showProgress,
    autoAdvance: store.uiState.autoAdvance,

    // Progress info
    completedComponents: Object.values(store.componentStates).filter(
      c => c.isCompleted
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

// Hook for component-specific state
export const useComponentState = (componentId: string) => {
  const store = useLearningSessionStore();

  return {
    state: store.componentStates[componentId],
    note: store.sessionNotes[componentId],
    isBookmarked: store.bookmarks.includes(componentId),
    timeSpent: store.getComponentTimeSpent(componentId),

    // Actions
    updateState: (updates: Partial<ComponentState>) =>
      store.updateComponentState(componentId, updates),
    start: () => store.startComponent(componentId),
    complete: (isCorrect?: boolean, userAnswer?: any) =>
      store.completeComponent(componentId, isCorrect, userAnswer),
    addNote: (note: string) => store.addNote(componentId, note),
    removeNote: () => store.removeNote(componentId),
    toggleBookmark: () => store.toggleBookmark(componentId),
  };
};
