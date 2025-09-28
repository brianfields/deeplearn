/**
 * User Module Public Interface
 *
 * Exposes a narrow contract for other modules to interact with the user
 * service. Pure forwarder with no logic per modular architecture rules.
 */

import type {
  LoginRequest,
  RegisterRequest,
  UpdateProfileRequest,
  User,
} from './models';
import { UserService } from './service';
import { UserIdentityService } from './identity';

export interface UserProvider {
  register(request: RegisterRequest): Promise<User>;
  login(request: LoginRequest): Promise<User>;
  logout(): Promise<void>;
  getProfile(userId: number): Promise<User | null>;
  updateProfile(userId: number, request: UpdateProfileRequest): Promise<User>;
}

export function userProvider(): UserProvider {
  const service = new UserService();
  return {
    register: service.register.bind(service),
    login: service.login.bind(service),
    logout: service.logout.bind(service),
    getProfile: service.getProfile.bind(service),
    updateProfile: service.updateProfile.bind(service),
  };
}

export interface UserIdentityProvider {
  getCurrentUser(): Promise<User | null>;
  setCurrentUser(user: User | null): Promise<void>;
  getCurrentUserId(): Promise<string>;
  clear(): Promise<void>;
}

export function userIdentityProvider(): UserIdentityProvider {
  const service = new UserIdentityService();
  return {
    getCurrentUser: service.getCurrentUser.bind(service),
    setCurrentUser: service.setCurrentUser.bind(service),
    getCurrentUserId: service.getCurrentUserId.bind(service),
    clear: service.clear.bind(service),
  };
}

export type {
  User,
  LoginRequest,
  RegisterRequest,
  UpdateProfileRequest,
} from './models';
export { AuthProvider, useAuth } from './context';
export { DEFAULT_ANONYMOUS_USER_ID } from './identity';
