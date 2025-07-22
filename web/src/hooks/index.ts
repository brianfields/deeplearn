/**
 * Hooks Module Index
 *
 * This file provides a clean interface to all custom React hooks.
 * Hooks encapsulate stateful logic and provide easy-to-use interfaces
 * for components.
 *
 * Usage:
 * ```typescript
 * import { useLearningPaths, useConversation } from '@/hooks'
 * ```
 */

// Dashboard hooks
export { default as useBiteSizedTopics } from './dashboard/useBiteSizedTopics'

// Learning hooks
export { useDuolingoLearning } from './learning/useDuolingoLearning'
export { default as useDuolingoLearning } from './learning/useDuolingoLearning'

// Re-export conversation hook (if it exists)
export { default as useConversation } from './useConversation'

// Re-export hook option types for convenience
export type { UseConversationOptions } from './useConversation'