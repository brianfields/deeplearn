import { infrastructureProvider } from '../infrastructure/public';
import type { User } from './models';

const STORAGE_KEY = 'deeplearn/mobile/current-user';
export const DEFAULT_ANONYMOUS_USER_ID = 'anonymous';

export class UserIdentityService {
  constructor(private infrastructure = infrastructureProvider()) {}

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

  async setCurrentUser(user: User | null): Promise<void> {
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

  async getCurrentUserId(): Promise<string> {
    const user = await this.getCurrentUser();
    if (user && user.id !== undefined && user.id !== null) {
      return String(user.id);
    }
    return DEFAULT_ANONYMOUS_USER_ID;
  }

  async clear(): Promise<void> {
    await this.setCurrentUser(null);
  }
}
