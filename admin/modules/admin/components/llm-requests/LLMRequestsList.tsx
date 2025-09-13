/**
 * LLM Requests List Component
 *
 * Displays paginated list of LLM requests.
 */

'use client';

import Link from 'next/link';
import { useLLMRequests } from '../../queries';
import { useLLMRequestFilters, useAdminStore } from '../../store';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { formatDate, formatExecutionTime, formatCost, formatTokens } from '@/lib/utils';

export function LLMRequestsList() {
  const filters = useLLMRequestFilters();
  const { setLLMRequestFilters } = useAdminStore();

  const { data: requests, isLoading, error, refetch } = useLLMRequests(filters);

  const handlePageChange = (newPage: number) => {
    setLLMRequestFilters({ page: newPage });
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setLLMRequestFilters({ page: 1, page_size: newPageSize });
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading LLM requests..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load LLM requests. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  const requestsList = requests?.requests || [];
  const totalCount = requests?.total_count || 0;
  const currentPage = requests?.page || filters.page || 1;
  const pageSize = requests?.page_size || filters.page_size || 10;
  const hasNext = requests?.has_next || false;

  return (
    <div className="space-y-6">
      {/* Header with pagination info */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-700">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} LLM requests
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <label htmlFor="pageSize" className="text-sm text-gray-700">
            Per page:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* LLM requests table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {requestsList.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
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
            <h3 className="mt-2 text-sm font-medium text-gray-900">No LLM requests</h3>
            <p className="mt-1 text-sm text-gray-500">
              No LLM requests have been made yet.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider / Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cached
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {requestsList.map((request) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {request.provider}
                          </div>
                          <div className="text-sm text-gray-500">
                            {request.model}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={request.status} size="sm" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(request.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatExecutionTime(request.execution_time_ms)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div>{formatTokens(request.tokens_used)}</div>
                        {request.input_tokens && request.output_tokens && (
                          <div className="text-xs text-gray-500">
                            {formatTokens(request.input_tokens)} in / {formatTokens(request.output_tokens)} out
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCost(request.cost_estimate)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {request.cached ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Cached
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Fresh
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        href={`/llm-requests/${request.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination controls */}
      {totalCount > pageSize && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Page {currentPage} of {Math.ceil(totalCount / pageSize)}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!hasNext}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
