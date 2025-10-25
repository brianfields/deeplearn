/**
 * Admin User Detail Component
 *
 * Shows detailed information about a specific user and allows updates.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useAdminUser, useUpdateAdminUser } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { formatDate } from '@/lib/utils';
import { StatusBadge } from '../shared/StatusBadge';

interface UserDetailProps {
  userId: number | string;
}

export function UserDetail({ userId }: UserDetailProps) {
  const { data: user, isLoading, error, refetch } = useAdminUser(userId);
  const updateUser = useUpdateAdminUser();

  const [name, setName] = useState('');
  const [role, setRole] = useState('user');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (user) {
      setName(user.name ?? '');
      setRole(user.role ?? 'user');
      setIsActive(user.is_active);
    }
  }, [user]);

  const ownedUnits = user?.owned_units ?? [];
  const recentSessions = user?.recent_sessions ?? [];
  const recentRequests = user?.recent_llm_requests ?? [];
  const recentConversations = user?.recent_conversations ?? [];

  const isUpdating = updateUser.isPending;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!user) {
      return;
    }

    await updateUser.mutateAsync({
      userId: user.id,
      payload: {
        name,
        role,
        is_active: isActive,
      },
    });
    refetch();
  };

  const associationSummary = useMemo(() => {
    if (!user) {
      return null;
    }
    return [
      { label: 'Owned units', value: user.associations.owned_unit_count },
      { label: 'Shared globally', value: user.associations.owned_global_unit_count },
      { label: 'Learning sessions', value: user.associations.learning_session_count },
      { label: 'LLM requests', value: user.associations.llm_request_count },
    ];
  }, [user]);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading user details..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load user details. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  if (!user) {
    return (
      <div className="space-y-4">
        <p className="text-gray-600">We couldn&apos;t find a user with that identifier.</p>
        <Link href="/users" className="text-blue-600 hover:text-blue-500">
          ← Back to users
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <Link href="/users" className="text-sm text-gray-500 hover:text-gray-700">
            ← Back to users
          </Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">{user.name || user.email}</h1>
          <p className="text-gray-600">User ID: {user.id}</p>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
            <span>Created: {formatDate(user.created_at)}</span>
            <span>Updated: {formatDate(user.updated_at)}</span>
            <span>Status: {user.is_active ? 'Active' : 'Inactive'}</span>
            <span>Role: {user.role || 'user'}</span>
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Associations</h2>
          <dl className="mt-4 grid grid-cols-2 gap-4">
            {associationSummary?.map((item) => (
              <div key={item.label}>
                <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">{item.label}</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900">{item.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Account settings</h2>
          <p className="text-sm text-gray-500">Update name, role, or activation status.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="user-name" className="block text-sm font-medium text-gray-700">
              Display name
            </label>
            <input
              id="user-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="user-role" className="block text-sm font-medium text-gray-700">
              Role
            </label>
            <select
              id="user-role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex items-center space-x-3">
            <input
              id="user-active"
              type="checkbox"
              checked={isActive}
              onChange={(event) => setIsActive(event.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="user-active" className="text-sm font-medium text-gray-700">
              Active account
            </label>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            type="submit"
            disabled={isUpdating}
            className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isUpdating ? 'Saving...' : 'Save changes'}
          </button>
          {updateUser.isError && (
            <span className="text-sm text-red-600">Failed to update user. Please try again.</span>
          )}
          {updateUser.isSuccess && !isUpdating && (
            <span className="text-sm text-green-600">Changes saved.</span>
          )}
        </div>
      </form>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6 space-y-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Owned units</h2>
            <p className="text-sm text-gray-500">
              Units created by this user and their sharing status.
            </p>
          </div>
          {ownedUnits.length === 0 ? (
            <p className="text-sm text-gray-500">No owned units yet.</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {ownedUnits.map((unit) => (
                <li key={unit.id} className="py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Link
                        href={`/units/${unit.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-500"
                      >
                        {unit.title}
                      </Link>
                      <div className="text-xs text-gray-500">Updated {formatDate(unit.updated_at)}</div>
                    </div>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        unit.is_global ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {unit.is_global ? 'Global' : 'Personal'}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6 space-y-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Recent sessions</h2>
            <p className="text-sm text-gray-500">Latest learning sessions owned by this user.</p>
          </div>
          {recentSessions.length === 0 ? (
            <p className="text-sm text-gray-500">No recent sessions recorded.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Session
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Progress
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Started
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Completed
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {recentSessions.map((session) => (
                    <tr key={session.id}>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        <div className="font-medium">{session.lesson_id}</div>
                        <div className="text-xs text-gray-500">{session.status}</div>
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        {Math.round(session.progress_percentage)}%
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">{formatDate(session.started_at)}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{formatDate(session.completed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6 space-y-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Recent conversations</h2>
            <p className="text-sm text-gray-500">
              Learning coach conversations started by this user.
            </p>
          </div>
          {recentConversations.length === 0 ? (
            <p className="text-sm text-gray-500">No recent conversations.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Conversation
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last message
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Messages
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {recentConversations.map((conversation) => (
                    <tr key={conversation.id}>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        <Link
                          href={`/conversations/${conversation.id}`}
                          className="text-blue-600 hover:text-blue-500"
                        >
                          {conversation.title ?? conversation.id}
                        </Link>
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        <StatusBadge status={conversation.status} size="sm" />
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        {formatDate(conversation.last_message_at)}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">{conversation.message_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6 space-y-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Recent LLM requests</h2>
            <p className="text-sm text-gray-500">
              Requests submitted by this user across LLM services.
            </p>
          </div>
          {recentRequests.length === 0 ? (
            <p className="text-sm text-gray-500">No recent requests.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Request
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tokens
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {recentRequests.map((request) => (
                    <tr key={request.id}>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        <Link href={`/llm-requests/${request.id}`} className="text-blue-600 hover:text-blue-500">
                          {request.id}
                        </Link>
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">{request.model}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{formatDate(request.created_at)}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{request.tokens_used ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
