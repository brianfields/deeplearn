/**
 * LLM Requests List Component
 *
 * Displays paginated list of LLM requests.
 */

'use client';

import { useLLMRequests } from '../../queries';
import { useLLMRequestFilters, useAdminStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { DetailViewTable, type DetailViewTableColumn } from '../shared/DetailViewTable';
import { formatDate, formatExecutionTime, formatCost, formatTokens } from '@/lib/utils';
import type { LLMRequestSummary } from '../../models';

export function LLMRequestsList(): JSX.Element {
  const filters = useLLMRequestFilters();
  const { setLLMRequestFilters } = useAdminStore();

  const { data, isLoading, error, refetch } = useLLMRequests(filters);

  const handlePageChange = (newPage: number) => {
    setLLMRequestFilters({ page: newPage });
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setLLMRequestFilters({ page: 1, page_size: newPageSize });
  };

  const requestsList = data?.requests ?? [];
  const totalCount = data?.total_count ?? 0;
  const currentPage = data?.page ?? filters.page ?? 1;
  const pageSize = data?.page_size ?? filters.page_size ?? 10;
  const hasNext = data?.has_next ?? false;
  const totalPages = pageSize > 0 ? Math.ceil(totalCount / pageSize) : 1;

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
        d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
      />
    </svg>
  );

  const columns: DetailViewTableColumn<LLMRequestSummary>[] = [
    {
      key: 'provider_model',
      label: 'Provider / Model',
      render: (request) => (
        <div>
          <div className="text-sm font-medium text-gray-900">{request.provider}</div>
          <div className="text-sm text-gray-500">{request.model}</div>
        </div>
      ),
    },
    {
      key: 'user_id',
      label: 'User',
      render: (request) => request.user_id ?? '—',
    },
    {
      key: 'status',
      label: 'Status',
      render: (request) => <StatusBadge status={request.status} size="sm" />,
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (request) => formatDate(request.created_at),
    },
    {
      key: 'duration',
      label: 'Duration',
      render: (request) => formatExecutionTime(request.execution_time_ms),
    },
    {
      key: 'tokens',
      label: 'Tokens',
      render: (request) => {
        if (request.input_tokens && request.output_tokens) {
          return (
            <div>
              <div>{formatTokens(request.tokens_used)}</div>
              <div className="text-xs text-gray-500">
                {formatTokens(request.input_tokens)} in / {formatTokens(request.output_tokens)} out
              </div>
            </div>
          );
        }
        return formatTokens(request.tokens_used);
      },
    },
    {
      key: 'cost',
      label: 'Cost',
      render: (request) => formatCost(request.cost_estimate),
    },
    {
      key: 'cached',
      label: 'Cached',
      render: (request) =>
        request.cached ? (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Cached
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            Fresh
          </span>
        ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header with pagination info */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-700">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} LLM requests
          </p>
        </div>
      </div>

      {/* LLM requests table */}
      <DetailViewTable
        data={requestsList}
        columns={columns}
        getRowId={(request) => request.id}
        getDetailHref={(request) => `/llm-requests/${request.id}`}
        isLoading={isLoading}
        error={error}
        emptyMessage="No LLM requests have been made yet."
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
