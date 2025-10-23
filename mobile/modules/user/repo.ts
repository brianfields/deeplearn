/**
 * User Module Repository
 *
 * Handles HTTP requests to the backend user routes. Returns API wire
 * formats which are converted to DTOs in the service layer.
 */

import { infrastructureProvider } from '../infrastructure/public';
import type { ApiAuthenticationResult, ApiUser, User } from './models';

const USER_BASE = '/api/v1/users';
export const STORAGE_KEY = 'deeplearn/mobile/current-user';

export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UpdateProfilePayload {
  name?: string;
  password?: string;
}

export class UserRepo {
  private infrastructure = infrastructureProvider();

  async register(payload: RegisterPayload): Promise<ApiUser> {
    const endpoint = `${USER_BASE}/register`;
    return this.infrastructure.request<ApiUser>(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        email: payload.email,
        password: payload.password,
        name: payload.name,
      }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async login(payload: LoginPayload): Promise<ApiAuthenticationResult> {
    const endpoint = `${USER_BASE}/login`;
    return this.infrastructure.request<ApiAuthenticationResult>(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        email: payload.email,
        password: payload.password,
      }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async getProfile(userId: number): Promise<ApiUser> {
    const endpoint = `${USER_BASE}/profile?user_id=${encodeURIComponent(
      String(userId)
    )}`;
    return this.infrastructure.request<ApiUser>(endpoint, {
      method: 'GET',
    });
  }

  async updateProfile(
    userId: number,
    payload: UpdateProfilePayload
  ): Promise<ApiUser> {
    const endpoint = `${USER_BASE}/profile?user_id=${encodeURIComponent(
      String(userId)
    )}`;
    return this.infrastructure.request<ApiUser>(endpoint, {
      method: 'PUT',
      body: JSON.stringify({
        ...(payload.name !== undefined ? { name: payload.name } : {}),
        ...(payload.password !== undefined
          ? { password: payload.password }
          : {}),
      }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const stored = await this.infrastructure.getStorageItem(STORAGE_KEY);
      if (!stored) {
        return null;
      }

      const parsed = JSON.parse(stored) as User;
      if (!parsed || typeof parsed !== 'object' || parsed.id === undefined) {
        return null;
      }

      return parsed;
    } catch (error) {
      console.warn('[UserIdentityService] Failed to load current user:', error);
      return null;
    }
  }

  async saveCurrentUser(user: User | null): Promise<void> {
    try {
      if (user) {
        await this.infrastructure.setStorageItem(
          STORAGE_KEY,
          JSON.stringify(user)
        );
      } else {
        await this.infrastructure.removeStorageItem(STORAGE_KEY);
      }
    } catch (error) {
      console.warn(
        '[UserIdentityService] Failed to persist current user:',
        error
      );
    }
  }
}
