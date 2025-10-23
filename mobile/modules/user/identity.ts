import type { User } from './models';
import { UserRepo } from './repo';

export const DEFAULT_ANONYMOUS_USER_ID = 'anonymous';

export class UserIdentityService {
  private cachedUser: User | null = null;

  constructor(private repo: UserRepo = new UserRepo()) {}

  async getCurrentUser(): Promise<User | null> {
    const user = await this.repo.getCurrentUser();
    this.cachedUser = user;
    return user;
  }

  async setCurrentUser(user: User | null): Promise<void> {
    this.cachedUser = user;
    await this.repo.saveCurrentUser(user);
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
    await this.repo.saveCurrentUser(null);
  }
}
