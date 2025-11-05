'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
  readonly onPageSizeChange?: (pageSize: number) => void;
  readonly pageOptions?: number[];
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
  onPageSizeChange,
  pageOptions,
  className = '',
  rowClassName = '',
}: DetailViewTableProps<T>): JSX.Element {
  const router = useRouter();

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
                  <tr
                    key={id}
                    onClick={() => {
                      router.push(detailHref);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        router.push(detailHref);
                      }
                    }}
                    className={`cursor-pointer hover:bg-gray-50 ${rowClassName}`}
                    role="button"
                    tabIndex={0}
                  >
                    {columns.map((column) => (
                      <td
                        key={`${id}-${column.key}`}
                        className={`px-6 py-4 text-sm text-gray-900 ${column.className ?? ''}`}
                      >
                        {column.render(item)}
                      </td>
                    ))}
                    <td className="relative px-6 py-4 text-right text-sm font-medium whitespace-nowrap">
                      <Link
                        href={detailHref}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center justify-center w-6 h-6 text-gray-400 hover:text-gray-600 transition-colors"
                        title="Open details"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5l7 7-7 7"
                          />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {pagination && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow px-6 py-4">
          <div className="flex items-center gap-6">
            <div className="text-sm text-gray-500">
              Showing {(pagination.currentPage - 1) * pagination.pageSize + 1} to {Math.min(pagination.currentPage * pagination.pageSize, pagination.totalCount)} of {pagination.totalCount}{' '}
              {pagination.totalCount === 1 ? 'item' : 'items'}
            </div>

            {pageOptions && onPageSizeChange && (
              <div className="flex items-center gap-2">
                <label htmlFor="page-size" className="text-sm text-gray-600">
                  Per page:
                </label>
                <select
                  id="page-size"
                  value={pagination.pageSize}
                  onChange={(e) => onPageSizeChange(parseInt(e.target.value))}
                  className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
                >
                  {pageOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {pagination.totalPages > 1 && onPageChange && (
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
          )}
        </div>
      )}
    </div>
  );
}
