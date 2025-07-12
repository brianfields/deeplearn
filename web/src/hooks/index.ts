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
export {
  useLearningPaths,
  useLearningPath
} from './useLearningPaths'

// Conversation hooks
export {
  useConversation,
  useConversationProgress,
  useConversationStats
} from './useConversation'

// Re-export hook option types for convenience
export type { UseConversationOptions } from './useConversation'