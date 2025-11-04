'use client';

import { Fragment, ReactNode, useState } from 'react';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

export interface ExpandableTableColumn<T> {
  readonly key: string;
  readonly label: string;
  readonly className?: string;
  readonly render: (item: T) => ReactNode;
}

interface ExpandableTableProps<T> {
  readonly data: T[];
  readonly columns: ExpandableTableColumn<T>[];
  readonly renderExpandedContent: (item: T) => ReactNode;
  readonly getRowId: (item: T) => string;
  readonly isLoading?: boolean;
  readonly error?: Error | null;
  readonly emptyMessage?: string;
  readonly emptyIcon?: ReactNode;
  readonly onRetry?: () => void;
  readonly className?: string;
  readonly rowClassName?: string;
}

/**
 * Reusable component for tables with expandable rows.
 * Used when clicking a row should expand inline details below it.
 *
 * @example
 * <ExpandableTable
 *   data={conversations}
 *   columns={[
 *     { key: 'title', label: 'Title', render: (c) => c.title },
 *     { key: 'type', label: 'Type', render: (c) => c.type },
 *   ]}
 *   renderExpandedContent={(c) => <ConversationDetails {...c} />}
 *   getRowId={(c) => c.id}
 * />
 */
export function ExpandableTable<T>({
  data,
  columns,
  renderExpandedContent,
  getRowId,
  isLoading = false,
  error = null,
  emptyMessage = 'No items found.',
  emptyIcon,
  onRetry,
  className = '',
  rowClassName = '',
}: ExpandableTableProps<T>): JSX.Element {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleExpanded = (id: string) => {
    setExpandedRows((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

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
    <div className={`bg-white shadow rounded-lg overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-10 px-4 py-3 text-left" aria-label="Expand row">
                {/* Spacer for expand button */}
              </th>
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
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {data.map((item) => {
              const id = getRowId(item);
              const isExpanded = expandedRows.has(id);

              return (
                <Fragment key={id}>
                  <tr className={`hover:bg-gray-50 ${rowClassName}`}>
                    <td className="w-10 px-4 py-4 text-center">
                      <button
                        type="button"
                        onClick={() => toggleExpanded(id)}
                        className="rounded-full border border-gray-200 p-1 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
                        aria-label={isExpanded ? 'Collapse row' : 'Expand row'}
                      >
                        <svg
                          className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : 'rotate-0'}`}
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
                      </button>
                    </td>
                    {columns.map((column) => (
                      <td
                        key={`${id}-${column.key}`}
                        className={`px-6 py-4 text-sm text-gray-900 ${column.className ?? ''}`}
                      >
                        {column.render(item)}
                      </td>
                    ))}
                  </tr>
                  {isExpanded && (
                    <tr>
                      <td colSpan={columns.length + 1} className="px-6 pb-6 pt-2">
                        {renderExpandedContent(item)}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
