'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

type AdminUser = {
  id: number;
  email: string;
  name: string;
  role: string;
};

interface AdminAuthContextValue {
  user: AdminUser | null;
  signIn(user: AdminUser): void;
  signOut(): void;
  isHydrated: boolean;
}

const STORAGE_KEY = 'deeplearn/admin/current-user';

const AdminAuthContext = createContext<AdminAuthContextValue | undefined>(
  undefined
);

function readStoredUser(): AdminUser | null {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return null;
    }
    const parsed = JSON.parse(stored) as AdminUser;
    if (!parsed || typeof parsed !== 'object' || parsed.id === undefined) {
      return null;
    }
    return parsed;
  } catch (error) {
    console.warn('[AdminAuth] Failed to parse stored user', error);
    return null;
  }
}

export function AdminAuthProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    const storedUser = readStoredUser();
    if (storedUser) {
      setUser(storedUser);
    }
    setIsHydrated(true);
  }, []);

  const signIn = useCallback((nextUser: AdminUser) => {
    setUser(nextUser);
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
      } catch (error) {
        console.warn('[AdminAuth] Failed to persist user', error);
      }
    }
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo<AdminAuthContextValue>(
    () => ({ user, signIn, signOut, isHydrated }),
    [user, signIn, signOut, isHydrated]
  );

  return (
    <AdminAuthContext.Provider value={value}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth(): AdminAuthContextValue {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
}
