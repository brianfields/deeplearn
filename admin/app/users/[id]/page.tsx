/**
 * Admin User Detail Page
 *
 * Wraps the user detail component for the given identifier.
 */

'use client';

import { useParams } from 'next/navigation';
import { UserDetail } from '@/modules/admin/components/users/UserDetail';

export default function UserDetailPage() {
  const params = useParams<{ id: string }>();
  const userId = params?.id;

  if (!userId) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold text-gray-900">User not found</h1>
        <p className="text-gray-600">The requested user identifier was not provided.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <UserDetail userId={userId} />
    </div>
  );
}
