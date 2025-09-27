/**
 * Root Layout for Admin Dashboard
 *
 * Provides global layout, providers, and navigation structure.
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { QueryProvider } from '@/lib/query-client';
import { AdminAuthProvider } from '@/modules/admin/components/auth/AdminAuthProvider';
import { AdminShell } from '@/modules/admin/components/shared/AdminShell';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Admin Dashboard - DeepLearn',
  description: 'Administrative dashboard for monitoring and managing the learning platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <AdminAuthProvider>
            <AdminShell>{children}</AdminShell>
          </AdminAuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
