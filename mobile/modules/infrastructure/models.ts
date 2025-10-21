/**
 * Infrastructure Module - Models
 *
 * Types and DTOs for infrastructure services.
 * No business logic - types only.
 */

// HTTP Client Types
export interface HttpClientConfig {
  baseURL: string;
  timeout: number;
  headers?: Record<string, string>;
  retryAttempts?: number;
}

export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  useCache?: boolean;
  retryAttempts?: number;
}

export interface ApiResponse<T = unknown> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  message: string;
  code?: string;
  status: number;
  details?: unknown;
}

// Storage Types (for non-React Query data)
export interface StorageConfig {
  prefix: string;
}

export interface StorageStats {
  size: number;
  entries: number;
}

// Network Types
export interface NetworkStatus {
  isConnected: boolean;
  type?: string;
  isInternetReachable?: boolean;
}

// Infrastructure DTOs
export interface InfrastructureHealth {
  httpClient: boolean;
  storage: boolean;
  network: boolean;
  timestamp: number;
}

// SQLite helpers
export interface SQLiteMigration {
  id: number;
  statements: string[];
}

export interface SQLiteConfig {
  databaseName: string;
  migrations: SQLiteMigration[];
  enableForeignKeys?: boolean;
}

export interface SQLiteResultSet<T = Record<string, unknown>> {
  rows: T[];
  rowsAffected: number;
  insertId?: number | null;
}

export interface FileInfo {
  exists: boolean;
  uri?: string;
  size?: number;
  modificationTime?: number;
}

export interface FileDownloadOptions {
  skipIfExists?: boolean;
}

export interface FileDownloadResult {
  uri: string;
  status: 'completed' | 'failed';
  bytesWritten?: number;
}
