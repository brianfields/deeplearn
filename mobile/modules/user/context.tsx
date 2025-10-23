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
import { userIdentityProvider } from './public';
import { offlineCacheProvider } from '../offline_cache/public';

interface AuthContextValue {
  user: User | null;
  signIn(user: User): Promise<void>;
  signOut(): Promise<void>;
  isHydrated: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);
  const identity = useMemo(() => userIdentityProvider(), []);

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

          // Local-first: Don't sync automatically on app start
          // User can explicitly sync via pull-to-refresh if needed
          console.log(
            '[Auth] App started with logged-in user (local-first mode)',
            {
              userId: storedUser.id,
              email: storedUser.email,
            }
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

      // Local-first: Don't sync automatically after sign-in
      // User can explicitly sync via pull-to-refresh if needed
      console.log('[Auth] User signed in (local-first mode)', {
        userId: nextUser.id,
        email: nextUser.email,
      });
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

    // Clear all cached units when signing out
    try {
      const cache = offlineCacheProvider();
      await cache.clearAll();
      console.log('[Auth] Cleared offline cache on sign-out');
    } catch (error) {
      console.warn('[Auth] Failed to clear cache on sign-out', error);
    }
  }, [identity, queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signIn,
      signOut,
      isHydrated,
      isAuthenticated: !!user,
    }),
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
