/**
 * Utilities Module Index
 *
 * This file provides a clean interface to all utility functions.
 * Utilities are pure functions that perform common operations
 * without side effects.
 *
 * Usage:
 * ```typescript
 * import { formatDuration, validateEmail } from '@/utils'
 * ```
 */

// Export formatting utilities
export {
  formatDuration,
  formatRelativeTime,
  formatDate,
  formatTime,
  formatPercentage,
  formatNumber,
  truncateText,
  titleCase,
  camelToReadable,
  formatFileSize,
  formatCurrency,
  getInitials,
  formatProgressText
} from './formatting'

// Export validation utilities
export {
  validateEmail,
  validateRequired,
  validateMinLength,
  validateMaxLength,
  validateLearningPathTopic,
  validateUserLevel,
  validateChatMessage,
  validateUrl,
  validatePositiveNumber,
  validateInteger,
  validateRange,
  validatePercentage,
  sanitizeHtml,
  sanitizeUserInput,
  isValidText,
  validateFile,
  debounceValidation,
  type ValidationResult,
  type FileValidationOptions
} from './validation'

// Re-export the original cn utility for className merging
export { cn } from './cn'