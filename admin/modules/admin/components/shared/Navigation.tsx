/**
 * Navigation Component
 *
 * Main navigation bar for the admin dashboard.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAdminAuth } from '../auth/AdminAuthProvider';

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/',
    description: 'Overview and system metrics',
  },
  {
    name: 'Users',
    href: '/users',
    description: 'Manage learners and administrators',
  },
  {
    name: 'Units',
    href: '/units',
    description: 'Browse units and their lessons',
  },
  {
    name: 'Tasks',
    href: '/tasks',
    description: 'Track background tasks and workers',
  },
  {
    name: 'Flow Runs',
    href: '/flows',
    description: 'Monitor flow executions',
  },
  {
    name: 'Conversations',
    href: '/conversations',
    description: 'Review learning coach conversations',
  },
  {
    name: 'LLM Requests',
    href: '/llm-requests',
    description: 'View LLM request details',
  },
];

export function Navigation() {
  const pathname = usePathname();
  const { user, signOut } = useAdminAuth();

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-xl font-bold text-gray-900">
              Lantern Room Admin
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-8">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== '/' && pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                  title={item.description}
                >
                  {item.name}
                </Link>
              );
            })}
          </div>

          {/* Status Indicator */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="hidden sm:flex flex-col items-end">
                <span className="text-sm font-medium text-gray-900">
                  {user.name || user.email}
                </span>
                <span className="text-xs text-gray-500 capitalize">
                  {user.role}
                </span>
              </div>
            )}
            <button
              type="button"
              onClick={signOut}
              className="inline-flex items-center rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            >
              Sign out
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Online</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
