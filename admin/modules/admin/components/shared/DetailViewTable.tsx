'use client';

import Link from 'next/link';
import { ReactNode } from 'react';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

export interface DetailViewTableColumn<T> {
  readonly key: string;
  readonly label: string;
  readonly className?: string;
  readonly render: (item: T) => ReactNode;
}

interface PaginationInfo {
  readonly currentPage: number;
  readonly totalPages: number;
  readonly totalCount: number;
  readonly pageSize: number;
  readonly hasNext: boolean;
}

interface DetailViewTableProps<T> {
  readonly data: T[];
  readonly columns: DetailViewTableColumn<T>[];
  readonly getRowId: (item: T) => string;
  readonly getDetailHref: (item: T) => string;
  readonly isLoading?: boolean;
  readonly error?: Error | null;
  readonly emptyMessage?: string;
  readonly emptyIcon?: ReactNode;
  readonly onRetry?: () => void;
  readonly pagination?: PaginationInfo;
  readonly onPageChange?: (page: number) => void;
  readonly className?: string;
  readonly rowClassName?: string;
}

/**
 * Reusable component for tables that link to detail view pages.
 * Used when clicking "View details" should navigate to a separate page.
 * Includes optional pagination controls.
 *
 * @example
 * <DetailViewTable
 *   data={users}
 *   columns={[
 *     { key: 'name', label: 'Name', render: (u) => u.name },
 *     { key: 'email', label: 'Email', render: (u) => u.email },
 *   ]}
 *   getRowId={(u) => u.id}
 *   getDetailHref={(u) => `/users/${u.id}`}
 *   pagination={{
 *     currentPage: 1,
 *     totalPages: 5,
 *     totalCount: 100,
 *     pageSize: 20,
 *     hasNext: true,
 *   }}
 *   onPageChange={(page) => setPage(page)}
 * />
 */
export function DetailViewTable<T>({
  data,
  columns,
  getRowId,
  getDetailHref,
  isLoading = false,
  error = null,
  emptyMessage = 'No items found.',
  emptyIcon,
  onRetry,
  pagination,
  onPageChange,
  className = '',
  rowClassName = '',
}: DetailViewTableProps<T>): JSX.Element {
  if (isLoading && data.length === 0) {
    return <LoadingSpinner size="lg" text="Loading..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load data. Please try again."
        details={error instanceof Error ? error.message : undefined}
        onRetry={onRetry}
      />
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white shadow overflow-hidden">
        <div className="px-6 py-12 text-center">
          {emptyIcon && <div className="mb-4 flex justify-center">{emptyIcon}</div>}
          <p className="text-sm text-gray-500">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      column.className ?? ''
                    }`}
                  >
                    {column.label}
                  </th>
                ))}
                <th className="relative px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {data.map((item) => {
                const id = getRowId(item);
                const detailHref = getDetailHref(item);

                return (
                  <tr key={id} className={`hover:bg-gray-50 ${rowClassName}`}>
                    {columns.map((column) => (
                      <td
                        key={`${id}-${column.key}`}
                        className={`px-6 py-4 text-sm text-gray-900 ${column.className ?? ''}`}
                      >
                        {column.render(item)}
                      </td>
                    ))}
                    <td className="relative px-6 py-4 text-right text-sm font-medium whitespace-nowrap">
                      <Link href={detailHref} className="text-blue-600 hover:text-blue-500">
                        View details
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {pagination && pagination.totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Showing page {pagination.currentPage} of {pagination.totalPages} ({pagination.totalCount}{' '}
            {pagination.totalCount === 1 ? 'item' : 'items'})
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(pagination.currentPage - 1)}
              disabled={pagination.currentPage === 1}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page {pagination.currentPage} of {pagination.totalPages}
            </span>
            <button
              onClick={() => onPageChange(pagination.currentPage + 1)}
              disabled={!pagination.hasNext}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
