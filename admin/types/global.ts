/**
 * Global TypeScript type definitions for admin dashboard.
 *
 * Contains shared types used across the application.
 */

// Common utility types
export type Status = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type LLMStatus = 'pending' | 'completed' | 'failed';

export type UserLevel = 'beginner' | 'intermediate' | 'advanced';

// Pagination types
export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// Filter types
export interface DateRangeFilter {
  start_date?: Date;
  end_date?: Date;
}

export interface FlowRunFilters extends DateRangeFilter {
  status?: Status;
  flow_name?: string;
  user_id?: string;
}

export interface LLMRequestFilters extends DateRangeFilter {
  status?: LLMStatus;
  provider?: string;
  model?: string;
  user_id?: string;
}

export interface LessonFilters {
  user_level?: UserLevel;
  domain?: string;
  search?: string;
}

// API response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

// Error types
export interface ApiError {
  message: string;
  detail?: string;
  status_code?: number;
}

// Component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

// Loading and error states
export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

// Chart data types
export interface ChartDataPoint {
  name: string;
  value: number;
  date?: string;
}

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  label?: string;
}

// Navigation types
export interface NavItem {
  label: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string | number;
}

// Table types
export interface TableColumn<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'number';
  required?: boolean;
  options?: { label: string; value: string }[];
  placeholder?: string;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Export commonly used React types
export type { ReactNode, ComponentType, FC } from 'react';
