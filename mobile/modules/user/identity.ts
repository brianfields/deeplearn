import { infrastructureProvider } from '../infrastructure/public';
import type { User } from './models';

const STORAGE_KEY = 'deeplearn/mobile/current-user';
export const DEFAULT_ANONYMOUS_USER_ID = 'anonymous';

export class UserIdentityService {
  private cachedUser: User | null = null;

  constructor(private infrastructure = infrastructureProvider()) {}

  async getCurrentUser(): Promise<User | null> {
    try {
      const stored = await this.infrastructure.getStorageItem(STORAGE_KEY);
      if (!stored) {
        this.cachedUser = null;
        return null;
      }

      const parsed = JSON.parse(stored) as User;
      if (!parsed || typeof parsed !== 'object' || parsed.id === undefined) {
        this.cachedUser = null;
        return null;
      }

      this.cachedUser = parsed;
      return parsed;
    } catch (error) {
      console.warn('[UserIdentityService] Failed to load current user:', error);
      this.cachedUser = null;
      return null;
    }
  }

  async setCurrentUser(user: User | null): Promise<void> {
    this.cachedUser = user;
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

  /**
   * Get the current user ID synchronously from the cache.
   * Returns null if no user is logged in.
   * Note: This relies on getCurrentUser() or setCurrentUser() being called first.
   */
  getUserId(): number | null {
    return this.cachedUser?.id ?? null;
  }

  async getCurrentUserId(): Promise<string> {
    const user = await this.getCurrentUser();
    if (user && user.id !== undefined && user.id !== null) {
      return String(user.id);
    }
    return DEFAULT_ANONYMOUS_USER_ID;
  }

  async clear(): Promise<void> {
    this.cachedUser = null;
    await this.setCurrentUser(null);
  }
}
