/**
 * Admin Users Page
 *
 * Hosts the user list view with search and pagination.
 */

'use client';

import { UserList } from '@/modules/admin/components/users/UserList';

export default function UsersPage() {
  return (
    <div className="space-y-6">
      <UserList />
    </div>
  );
}
