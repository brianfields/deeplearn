import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { User } from './models';
import { userQueryKeys } from './queries';
import { UserIdentityService } from './identity';

interface AuthContextValue {
  user: User | null;
  signIn(user: User): Promise<void>;
  signOut(): Promise<void>;
  isHydrated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);
  const identity = useMemo(() => new UserIdentityService(), []);

  useEffect(() => {
    let isMounted = true;

    (async () => {
      try {
        const storedUser = await identity.getCurrentUser();
        if (isMounted && storedUser) {
          setUser(storedUser);
          queryClient.setQueryData(
            userQueryKeys.profile(storedUser.id),
            storedUser
          );
        }
      } catch (error) {
        console.warn('[Auth] Failed to load stored user', error);
      } finally {
        if (isMounted) {
          setIsHydrated(true);
        }
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [identity, queryClient]);

  const signIn = useCallback(
    async (nextUser: User) => {
      setUser(nextUser);
      queryClient.setQueryData(userQueryKeys.profile(nextUser.id), nextUser);

      try {
        await identity.setCurrentUser(nextUser);
      } catch (error) {
        console.warn('[Auth] Failed to persist user', error);
      }
    },
    [identity, queryClient]
  );

  const signOut = useCallback(async () => {
    setUser(null);
    try {
      await identity.setCurrentUser(null);
    } catch (error) {
      console.warn('[Auth] Failed to clear stored user', error);
    }
    queryClient.removeQueries({ queryKey: ['user'] });
  }, [identity, queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, signIn, signOut, isHydrated }),
    [user, signIn, signOut, isHydrated]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
