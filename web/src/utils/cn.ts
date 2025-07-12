/**
 * ClassName Utility
 *
 * This module provides the `cn` utility function for merging CSS classes.
 * It combines clsx for conditional classes with tailwind-merge for
 * deduplicating conflicting Tailwind classes.
 *
 * Usage:
 * ```typescript
 * cn('bg-red-500', condition && 'text-white', 'p-4')
 * ```
 */

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge CSS classes with conditional support and Tailwind deduplication
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}