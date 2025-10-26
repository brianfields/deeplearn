/**
 * Admin Module - Client State Management
 *
 * Zustand store for admin UI state management.
 * Handles filters, selections, and UI state.
 */

import { create } from 'zustand';

// ---- State Interfaces ----

interface AdminState {
  // Flow filters and UI state
  flowFilters: {
    status?: string;
    flow_name?: string;
    user_id?: string;
    date_range?: [Date, Date];
    page?: number;
    page_size?: number;
  };

  // Conversation filters
  conversationFilters: {
    status?: string;
    user_id?: string | number;
    page?: number;
    page_size?: number;
  };

  // Learning session filters
  learningSessionFilters: {
    status?: string;
    user_id?: string;
    lesson_id?: string;
    page?: number;
    page_size?: number;
  };

  // LLM request filters
  llmRequestFilters: {
    status?: string;
    provider?: string;
    model?: string;
    user_id?: string;
    date_range?: [Date, Date];
    page?: number;
    page_size?: number;
  };

  // Lesson filters
  lessonFilters: {
    learner_level?: string;
    search?: string;
    domain?: string;
    page?: number;
    page_size?: number;
  };

  // Global UI state
  selectedFlowId: string | null;
  selectedStepId: string | null;
  selectedLLMRequestId: string | null;
  selectedLessonId: string | null;

  // UI preferences
  showRawData: boolean;
  expandedSections: Set<string>;
}

interface AdminActions {
  // Flow actions
  setFlowFilters: (filters: Partial<AdminState['flowFilters']>) => void;
  clearFlowFilters: () => void;
  selectFlow: (id: string | null) => void;
  selectStep: (id: string | null) => void;

  // Conversation actions
  setConversationFilters: (filters: Partial<AdminState['conversationFilters']>) => void;
  clearConversationFilters: () => void;

  // Learning session actions
  setLearningSessionFilters: (filters: Partial<AdminState['learningSessionFilters']>) => void;
  clearLearningSessionFilters: () => void;

  // LLM request actions
  setLLMRequestFilters: (filters: Partial<AdminState['llmRequestFilters']>) => void;
  clearLLMRequestFilters: () => void;
  selectLLMRequest: (id: string | null) => void;

  // Lesson actions
  setLessonFilters: (filters: Partial<AdminState['lessonFilters']>) => void;
  clearLessonFilters: () => void;
  selectLesson: (id: string | null) => void;

  // UI actions
  toggleRawData: () => void;
  toggleSection: (sectionId: string) => void;
  expandSection: (sectionId: string) => void;
  collapseSection: (sectionId: string) => void;
  clearSelections: () => void;
}

// ---- Store Implementation ----

export const useAdminStore = create<AdminState & AdminActions>((set, get) => ({
  // Initial state
  flowFilters: {
    page: 1,
    page_size: 10,
  },
  conversationFilters: {
    page: 1,
    page_size: 50,
  },
  learningSessionFilters: {
    page: 1,
    page_size: 25,
  },
  llmRequestFilters: {
    page: 1,
    page_size: 10,
  },
  lessonFilters: {
    page: 1,
    page_size: 10,
    domain: undefined,
  },
  selectedFlowId: null,
  selectedStepId: null,
  selectedLLMRequestId: null,
  selectedLessonId: null,
  showRawData: false,
  expandedSections: new Set(),

  // Flow actions
  setFlowFilters: (filters) =>
    set((state) => ({
      flowFilters: { ...state.flowFilters, ...filters },
    })),

  clearFlowFilters: () =>
    set({
      flowFilters: {
        page: 1,
        page_size: 10,
      },
    }),

  selectFlow: (id) =>
    set({
      selectedFlowId: id,
      selectedStepId: null, // Clear step selection when flow changes
    }),

  selectStep: (id) => set({ selectedStepId: id }),

  // Conversation actions
  setConversationFilters: (filters) =>
    set((state) => ({
      conversationFilters: { ...state.conversationFilters, ...filters },
    })),

  clearConversationFilters: () =>
    set({
      conversationFilters: {
        page: 1,
        page_size: 50,
      },
    }),

  // Learning session actions
  setLearningSessionFilters: (filters) =>
    set((state) => ({
      learningSessionFilters: { ...state.learningSessionFilters, ...filters },
    })),

  clearLearningSessionFilters: () =>
    set({
      learningSessionFilters: {
        page: 1,
        page_size: 25,
      },
    }),

  // LLM request actions
  setLLMRequestFilters: (filters) =>
    set((state) => ({
      llmRequestFilters: { ...state.llmRequestFilters, ...filters },
    })),

  clearLLMRequestFilters: () =>
    set({
      llmRequestFilters: {
        page: 1,
        page_size: 10,
      },
    }),

  selectLLMRequest: (id) => set({ selectedLLMRequestId: id }),

  // Lesson actions
  setLessonFilters: (filters) =>
    set((state) => ({
      lessonFilters: { ...state.lessonFilters, ...filters },
    })),

  clearLessonFilters: () =>
    set({
      lessonFilters: {
        page: 1,
        page_size: 10,
        domain: undefined,
      },
    }),

  selectLesson: (id) => set({ selectedLessonId: id }),

  // UI actions
  toggleRawData: () => set((state) => ({ showRawData: !state.showRawData })),

  toggleSection: (sectionId) => {
    const { expandedSections } = get();
    const newExpanded = new Set(expandedSections);

    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }

    set({ expandedSections: newExpanded });
  },

  expandSection: (sectionId) => {
    const { expandedSections } = get();
    const newExpanded = new Set(expandedSections);
    newExpanded.add(sectionId);
    set({ expandedSections: newExpanded });
  },

  collapseSection: (sectionId) => {
    const { expandedSections } = get();
    const newExpanded = new Set(expandedSections);
    newExpanded.delete(sectionId);
    set({ expandedSections: newExpanded });
  },

  clearSelections: () =>
    set({
      selectedFlowId: null,
      selectedStepId: null,
      selectedLLMRequestId: null,
      selectedLessonId: null,
    }),
}));

// ---- Selector Hooks ----

export const useFlowFilters = () => useAdminStore((state) => state.flowFilters);
export const useFlowSelection = () => useAdminStore((state) => ({
  selectedFlowId: state.selectedFlowId,
  selectedStepId: state.selectedStepId,
  selectFlow: state.selectFlow,
  selectStep: state.selectStep,
}));

export const useConversationFilters = () => useAdminStore((state) => state.conversationFilters);
export const useLearningSessionFilters = () => useAdminStore((state) => state.learningSessionFilters);

export const useLLMRequestFilters = () => useAdminStore((state) => state.llmRequestFilters);
export const useLLMRequestSelection = () => useAdminStore((state) => ({
  selectedLLMRequestId: state.selectedLLMRequestId,
  selectLLMRequest: state.selectLLMRequest,
}));

export const useLessonFilters = () => useAdminStore((state) => state.lessonFilters);
export const useLessonSelection = () => useAdminStore((state) => ({
  selectedLessonId: state.selectedLessonId,
  selectLesson: state.selectLesson,
}));

export const useUIState = () => useAdminStore((state) => ({
  showRawData: state.showRawData,
  expandedSections: state.expandedSections,
  toggleRawData: state.toggleRawData,
  toggleSection: state.toggleSection,
  expandSection: state.expandSection,
  collapseSection: state.collapseSection,
}));
