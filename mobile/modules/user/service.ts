/**
 * User Module Service
 *
 * Applies business rules and converts API wire formats into module DTOs.
 */

import type {
  LoginRequest,
  RegisterRequest,
  UpdateProfileRequest,
  User,
  ApiUser,
} from './models';
import { UserRepo } from './repo';

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export class UserService {
  constructor(private repo: UserRepo = new UserRepo()) {}

  async register(request: RegisterRequest): Promise<User> {
    this.assertEmail(request.email);
    this.assertPassword(request.password);
    const apiUser = await this.repo.register(request);
    return this.toDto(apiUser);
  }

  async login(request: LoginRequest): Promise<User> {
    this.assertEmail(request.email);
    if (!request.password.trim()) {
      throw this.createError('Password is required');
    }
    const result = await this.repo.login(request);
    return this.toDto(result.user);
  }

  async logout(): Promise<void> {
    // No backend endpoint yet; reserved for future token revocation.
    return Promise.resolve();
  }

  async getProfile(userId: number): Promise<User | null> {
    if (!Number.isFinite(userId) || userId <= 0) {
      return null;
    }
    try {
      const apiUser = await this.repo.getProfile(userId);
      return this.toDto(apiUser);
    } catch (error: any) {
      if (error?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  async updateProfile(
    userId: number,
    request: UpdateProfileRequest
  ): Promise<User> {
    if (!Number.isFinite(userId) || userId <= 0) {
      throw this.createError('A valid user id is required');
    }
    if (request.password !== undefined) {
      this.assertPassword(request.password);
    }
    const apiUser = await this.repo.updateProfile(userId, request);
    return this.toDto(apiUser);
  }

  private toDto(api: ApiUser): User {
    const createdAt = new Date(api.created_at);
    const updatedAt = new Date(api.updated_at);
    const role = (api.role || 'learner').toLowerCase();
    return {
      id: api.id,
      email: api.email,
      name: api.name,
      role: (api.role || 'learner') as User['role'],
      isActive: api.is_active,
      createdAt,
      updatedAt,
      displayName: api.name || api.email,
      isAdmin: role === 'admin',
    };
  }

  private assertEmail(email: string): void {
    if (!EMAIL_PATTERN.test(email)) {
      throw this.createError('A valid email address is required');
    }
  }

  private assertPassword(password: string): void {
    if (!password || password.length < 8) {
      throw this.createError('Password must be at least 8 characters long');
    }
  }

  private createError(message: string): Error {
    const error = new Error(message);
    (error as any).code = 'USER_SERVICE_ERROR';
    return error;
  }
}
