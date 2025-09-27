/**
 * User Module Repository
 *
 * Handles HTTP requests to the backend user routes. Returns API wire
 * formats which are converted to DTOs in the service layer.
 */

import { infrastructureProvider } from '../infrastructure/public';
import type { ApiAuthenticationResult, ApiUser } from './models';

const USER_BASE = '/api/v1/users';

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
}
