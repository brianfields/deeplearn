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

// Learning paths hooks
export { default as useBiteSizedTopics } from './useBiteSizedTopics'
export { default as useConversation } from './useConversation'
export { default as useLearningPaths } from './useLearningPaths'
export { default as useDuolingoLearning } from './useDuolingoLearning'

// Re-export hook option types for convenience
export type { UseConversationOptions } from './useConversation'