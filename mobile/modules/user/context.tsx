import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useQueryClient } from '@tanstack/react-query';
import type { User } from './models';
import { userQueryKeys } from './queries';

interface AuthContextValue {
  user: User | null;
  signIn(user: User): Promise<void>;
  signOut(): Promise<void>;
  isHydrated: boolean;
}

const STORAGE_KEY = 'deeplearn/mobile/current-user';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function loadStoredUser(): Promise<User | null> {
  try {
    const value = await AsyncStorage.getItem(STORAGE_KEY);
    if (!value) {
      return null;
    }

    const parsed = JSON.parse(value) as User;
    if (!parsed || typeof parsed !== 'object' || parsed.id === undefined) {
      return null;
    }

    return parsed;
  } catch (error) {
    console.warn('[Auth] Failed to load stored user', error);
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    let isMounted = true;

    loadStoredUser().then(storedUser => {
      if (isMounted && storedUser) {
        setUser(storedUser);
        queryClient.setQueryData(userQueryKeys.profile(storedUser.id), storedUser);
      }
      if (isMounted) {
        setIsHydrated(true);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [queryClient]);

  const signIn = useCallback(
    async (nextUser: User) => {
      setUser(nextUser);
      queryClient.setQueryData(userQueryKeys.profile(nextUser.id), nextUser);

      try {
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
      } catch (error) {
        console.warn('[Auth] Failed to persist user', error);
      }
    },
    [queryClient]
  );

  const signOut = useCallback(async () => {
    setUser(null);
    try {
      await AsyncStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.warn('[Auth] Failed to clear stored user', error);
    }
    queryClient.removeQueries({ queryKey: ['user'] });
  }, [queryClient]);

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
