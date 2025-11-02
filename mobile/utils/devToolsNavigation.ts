/**
 * Development Tools Navigation Configuration
 *
 * This module provides utilities for managing dev-only screens and navigation.
 * Development tools (cache management, database inspection, etc.) are separated
 * from user-facing screens to prevent accidental exposure in production builds.
 *
 * Usage:
 * - Wrap dev screens in __DEV__ conditionals
 * - Use getDevScreenOptions() for consistent dev tool styling
 */

import type { NativeStackNavigationOptions } from '@react-navigation/native-stack';
import { getScreenOptions } from './navigationOptions';

/**
 * Get screen options for development tool screens
 * Dev screens appear as overlays with modal presentation
 */
export function getDevScreenOptions(): NativeStackNavigationOptions {
  return {
    ...getScreenOptions('modal'),
    // Optionally add a visual indicator that this is a dev tool
    // by using card presentation or different animation timing
  };
}

/**
 * Helper to conditionally render dev screens only in development
 * @returns true if in development mode (can be used in conditionals)
 */
export const isDevMode = (): boolean => __DEV__;

/**
 * List of dev tool screen names for reference
 */
export const DEV_SCREEN_NAMES = {
  MANAGE_CACHE: 'ManageCache',
  SQLITE_DETAIL: 'SQLiteDetail',
  ASYNC_STORAGE_DETAIL: 'AsyncStorageDetail',
  FILE_SYSTEM_DETAIL: 'FileSystemDetail',
} as const;
