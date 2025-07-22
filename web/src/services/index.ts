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

// Learning services
export { duolingoLearningService } from './learning/learning-flow'

// Re-export other services
export * from './conversation'