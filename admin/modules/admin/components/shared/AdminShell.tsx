'use client';

import React from 'react';
import { Navigation } from './Navigation';
import { LoginPanel } from '../auth/LoginPanel';
import { useAdminAuth } from '../auth/AdminAuthProvider';

export function AdminShell({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const { user, isHydrated } = useAdminAuth();

  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <span className="text-gray-500 text-sm">Loading dashboard…</span>
      </div>
    );
  }

  if (!user) {
    return <LoginPanel />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
