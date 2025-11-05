/**
 * Admin Users Page
 *
 * Hosts the user list view with search and pagination.
 */

'use client';

import { useQueryClient } from '@tanstack/react-query';
import { UserList } from '@/modules/admin/components/users/UserList';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';
import { adminKeys } from '@/modules/admin/queries';

export default function UsersPage() {
  const queryClient = useQueryClient();

  const handleReload = () => {
    // Invalidate all user queries to trigger refetch
    void queryClient.invalidateQueries({ queryKey: adminKeys.users() });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Manage users and view their activity"
        onReload={handleReload}
      />
      <UserList />
    </div>
  );
}
