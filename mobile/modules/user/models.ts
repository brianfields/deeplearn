/**
 * User Module Models
 *
 * Defines DTOs used throughout the mobile application for user
 * authentication and profile management. Follows the modular architecture
 * guidelines where models are pure types with no logic.
 */

export type UserId = number;

export type UserRole = 'learner' | 'admin' | (string & {});

export interface ApiUser {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiAuthenticationResult {
  user: ApiUser;
}

export interface User {
  id: UserId;
  email: string;
  name: string;
  role: UserRole;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  displayName: string;
  isAdmin: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface UpdateProfileRequest {
  name?: string;
  password?: string;
}
