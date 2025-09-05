/**
 * Infrastructure Module API
 *
 * This module provides the public interface for the Infrastructure module.
 * Other modules should only import from this module_api package.
 */

// HTTP Client
export { useHttpClient } from './http';
export type { RequestConfig, HttpResponse, ApiError } from './http';

// Caching
export { useCache } from './cache';
export type { CacheConfig } from './cache';

// Public API exports - all exports are handled by the export statements above
