/**
 * User Module React Query Hooks
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  LoginRequest,
  RegisterRequest,
  UpdateProfileRequest,
  User,
} from './models';
import { UserService } from './service';

const service = new UserService();

export const userQueryKeys = {
  profile: (userId: number) => ['user', 'profile', userId] as const,
};

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: RegisterRequest) => service.register(request),
    onSuccess: user => {
      queryClient.setQueryData(userQueryKeys.profile(user.id), user);
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: LoginRequest) => service.login(request),
    onSuccess: user => {
      queryClient.setQueryData(userQueryKeys.profile(user.id), user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => service.logout(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['user', 'profile'] });
    },
  });
}

export function useProfile(userId: number) {
  return useQuery({
    queryKey: userQueryKeys.profile(userId),
    queryFn: () => service.getProfile(userId),
    enabled: Number.isFinite(userId) && userId > 0,
  });
}

export function useUpdateProfile(userId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateProfileRequest) =>
      service.updateProfile(userId, request),
    onSuccess: user => {
      queryClient.setQueryData(userQueryKeys.profile(user.id), user);
    },
  });
}

export type { User } from './models';
