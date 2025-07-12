/**
 * Services Module Index
 *
 * This file provides a clean interface to all business logic services.
 * Services handle complex operations and abstract API calls from components.
 *
 * Usage:
 * ```typescript
 * import { learningService, conversationService } from '@/services'
 * ```
 */

// Export learning service
export {
  LearningService,
  learningService,
  createLearningService,
  type CreateLearningPathOptions,
  type EnhancedLearningPath,
  type LearningStats
} from './learning'

// Export conversation service
export {
  ConversationService,
  conversationService,
  createConversationService,
  type ConversationHandlers,
  type ActiveConversation,
  type StartConversationOptions,
  type ConversationStats
} from './conversation'