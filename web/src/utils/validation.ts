/**
 * Validation Utilities
 *
 * This module provides utility functions for validating user input,
 * form data, and other data structures.
 *
 * All functions return boolean or validation result objects.
 */

import type { ValidationError, UserLevel } from '@/types'

/**
 * Validation result interface
 */
export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
}

/**
 * Email validation regex
 */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Validate email address
 */
export function validateEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim())
}

/**
 * Validate required field is not empty
 */
export function validateRequired(value: string | null | undefined, fieldName: string = 'Field'): ValidationError | null {
  if (!value || value.trim().length === 0) {
    return {
      field: fieldName.toLowerCase(),
      message: `${fieldName} is required`
    }
  }
  return null
}

/**
 * Validate minimum length
 */
export function validateMinLength(
  value: string,
  minLength: number,
  fieldName: string = 'Field'
): ValidationError | null {
  if (value.trim().length < minLength) {
    return {
      field: fieldName.toLowerCase(),
      message: `${fieldName} must be at least ${minLength} characters long`
    }
  }
  return null
}

/**
 * Validate maximum length
 */
export function validateMaxLength(
  value: string,
  maxLength: number,
  fieldName: string = 'Field'
): ValidationError | null {
  if (value.trim().length > maxLength) {
    return {
      field: fieldName.toLowerCase(),
      message: `${fieldName} must be less than ${maxLength} characters`
    }
  }
  return null
}

/**
 * Validate learning path topic
 */
export function validateLearningPathTopic(topic: string): ValidationResult {
  const errors: ValidationError[] = []

  const requiredError = validateRequired(topic, 'Topic')
  if (requiredError) {
    errors.push(requiredError)
  }

  if (topic) {
    const minLengthError = validateMinLength(topic, 3, 'Topic')
    if (minLengthError) {
      errors.push(minLengthError)
    }

    const maxLengthError = validateMaxLength(topic, 200, 'Topic')
    if (maxLengthError) {
      errors.push(maxLengthError)
    }

    // Check for inappropriate characters
    if (topic.includes('<') || topic.includes('>')) {
      errors.push({
        field: 'topic',
        message: 'Topic cannot contain HTML tags'
      })
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Validate user level
 */
export function validateUserLevel(level: string): ValidationResult {
  const validLevels: UserLevel[] = ['beginner', 'intermediate', 'advanced']

  if (!validLevels.includes(level as UserLevel)) {
    return {
      isValid: false,
      errors: [{
        field: 'userLevel',
        message: 'User level must be beginner, intermediate, or advanced'
      }]
    }
  }

  return {
    isValid: true,
    errors: []
  }
}

/**
 * Validate chat message
 */
export function validateChatMessage(message: string): ValidationResult {
  const errors: ValidationError[] = []

  const requiredError = validateRequired(message, 'Message')
  if (requiredError) {
    errors.push(requiredError)
  }

  if (message) {
    const maxLengthError = validateMaxLength(message, 2000, 'Message')
    if (maxLengthError) {
      errors.push(maxLengthError)
    }

    // Check for suspicious content
    const suspiciousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+\s*=/i
    ]

    if (suspiciousPatterns.some(pattern => pattern.test(message))) {
      errors.push({
        field: 'message',
        message: 'Message contains invalid content'
      })
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Validate URL format
 */
export function validateUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Validate positive number
 */
export function validatePositiveNumber(value: number): boolean {
  return typeof value === 'number' && value > 0 && !isNaN(value)
}

/**
 * Validate integer
 */
export function validateInteger(value: number): boolean {
  return Number.isInteger(value)
}

/**
 * Validate range
 */
export function validateRange(value: number, min: number, max: number): boolean {
  return value >= min && value <= max
}

/**
 * Validate percentage (0-100)
 */
export function validatePercentage(value: number): boolean {
  return validateRange(value, 0, 100)
}

/**
 * Sanitize HTML content
 */
export function sanitizeHtml(input: string): string {
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
}

/**
 * Validate and sanitize user input
 */
export function sanitizeUserInput(input: string): string {
  return input
    .trim()
    .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
    .substring(0, 1000) // Limit length
}

/**
 * Check if string contains only alphanumeric characters and common punctuation
 */
export function isValidText(text: string): boolean {
  const validTextRegex = /^[a-zA-Z0-9\s.,!?;:'"()-]+$/
  return validTextRegex.test(text)
}

/**
 * Validate file upload
 */
export interface FileValidationOptions {
  maxSize: number // in bytes
  allowedTypes: string[]
  allowedExtensions: string[]
}

export function validateFile(
  file: File,
  options: FileValidationOptions
): ValidationResult {
  const errors: ValidationError[] = []

  // Check file size
  if (file.size > options.maxSize) {
    errors.push({
      field: 'file',
      message: `File size must be less than ${Math.round(options.maxSize / 1024 / 1024)}MB`
    })
  }

  // Check file type
  if (options.allowedTypes.length > 0 && !options.allowedTypes.includes(file.type)) {
    errors.push({
      field: 'file',
      message: `File type ${file.type} is not allowed`
    })
  }

  // Check file extension
  if (options.allowedExtensions.length > 0) {
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!extension || !options.allowedExtensions.includes(extension)) {
      errors.push({
        field: 'file',
        message: `File extension must be one of: ${options.allowedExtensions.join(', ')}`
      })
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Debounce validation function
 */
export function debounceValidation<T extends any[]>(
  validationFn: (...args: T) => ValidationResult,
  delay: number = 300
): (...args: T) => Promise<ValidationResult> {
  let timeoutId: NodeJS.Timeout

  return (...args: T): Promise<ValidationResult> => {
    return new Promise((resolve) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        resolve(validationFn(...args))
      }, delay)
    })
  }
}