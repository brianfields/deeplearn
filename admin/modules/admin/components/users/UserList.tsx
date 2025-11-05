/**
 * Admin Users List Component
 *
 * Displays paginated list of users with association counts and search.
 */

'use client';

import { useMemo, useState } from 'react';
import { useAdminUsers } from '../../queries';
import type { UserListQuery } from '../../models';
import { DetailViewTable, type DetailViewTableColumn } from '../shared/DetailViewTable';
import { formatDate } from '@/lib/utils';
import type { UserSummary } from '../../models';

export function UserList(): JSX.Element {
  const [searchValue, setSearchValue] = useState('');
  const [activeSearch, setActiveSearch] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const params: UserListQuery = useMemo(() => {
    const trimmed = activeSearch?.trim();
    return {
      page,
      page_size: pageSize,
      search: trimmed ? trimmed : undefined,
    };
  }, [activeSearch, page, pageSize]);

  const { data, isLoading, error, refetch } = useAdminUsers(params);

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
    setActiveSearch(searchValue);
  };

  const handleClearSearch = () => {
    setSearchValue('');
    setActiveSearch(undefined);
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPage(1);
    // Note: pageSize state is managed through useMemo
  };

  const users = data?.users ?? [];
  const totalCount = data?.total_count ?? 0;
  const hasNext = data?.has_next ?? false;
  const currentPage = data?.page ?? page;
  const totalPages = totalCount > 0 ? Math.ceil(totalCount / pageSize) : 1;

  const PAGE_SIZE_OPTIONS = [10, 25, 50];

  const emptyIcon = (
    <svg
      className="h-12 w-12 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3a6 6 0 016-6h6a6 6 0 016 6m0 0h6"
      />
    </svg>
  );

  const columns: DetailViewTableColumn<UserSummary>[] = [
    {
      key: 'name',
      label: 'User',
      render: (user) => (
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-900">{user.name || 'Unnamed user'}</span>
          <span className="text-sm text-gray-500">{user.email}</span>
        </div>
      ),
    },
    {
      key: 'role',
      label: 'Role',
      render: (user) => <span className="capitalize">{user.role || 'user'}</span>,
    },
    {
      key: 'units',
      label: 'Units',
      render: (user) => (
        <div className="flex flex-col">
          <span>{user.associations.owned_unit_count} total</span>
          <span className="text-xs text-gray-500">{user.associations.owned_global_unit_count} shared</span>
        </div>
      ),
    },
    {
      key: 'sessions',
      label: 'Sessions',
      render: (user) => user.associations.learning_session_count,
    },
    {
      key: 'llm_requests',
      label: 'LLM Requests',
      render: (user) => user.associations.llm_request_count,
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (user) => formatDate(user.created_at),
    },
    {
      key: 'status',
      label: 'Status',
      render: (user) =>
        user.is_active ? (
          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
            Active
          </span>
        ) : (
          <span className="inline-flex items-center rounded-full bg-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-700">
            Inactive
          </span>
        ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
          <input
            type="search"
            value={searchValue}
            onChange={(event) => setSearchValue(event.target.value)}
            placeholder="Search by name or email"
            className="w-64 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Search
          </button>
          {activeSearch && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      <DetailViewTable
        data={users}
        columns={columns}
        getRowId={(user) => user.id.toString()}
        getDetailHref={(user) => `/users/${user.id}`}
        isLoading={isLoading}
        error={error}
        emptyMessage="Try adjusting your search or filters."
        emptyIcon={emptyIcon}
        onRetry={() => refetch()}
        pagination={{
          currentPage,
          totalPages,
          totalCount,
          pageSize,
          hasNext,
        }}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        pageOptions={PAGE_SIZE_OPTIONS}
      />
    </div>
  );
}
