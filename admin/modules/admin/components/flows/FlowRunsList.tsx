/**
 * Flow Runs List Component
 *
 * Displays paginated list of flow runs with basic controls.
 */

'use client';

import Link from 'next/link';
import { Fragment, useState } from 'react';
import { useFlowRun, useFlowRuns } from '../../queries';
import { useFlowFilters, useAdminStore } from '../../store';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { ReloadButton } from '../shared/ReloadButton';
import { FlowStepsList } from './FlowStepsList';
import {
  formatDate,
  formatExecutionTime,
  formatCost,
  formatTokens,
  formatPercentage,
} from '@/lib/utils';
import type { FlowRunDetails } from '../../models';

function deriveUnitId(flow: FlowRunDetails | undefined): string | null {
  if (!flow) {
    return null;
  }

  if (flow.unit_id) {
    return flow.unit_id;
  }

  const candidateKeys = ['unit_id', 'unitId', 'unit'];
  for (const key of candidateKeys) {
    const fromInputs = (flow.inputs as Record<string, unknown>)[key];
    if (typeof fromInputs === 'string' && fromInputs.trim().length > 0) {
      return fromInputs;
    }
  }

  const metadata = flow.flow_metadata as Record<string, unknown> | null;
  if (metadata) {
    for (const key of candidateKeys) {
      const value = metadata[key];
      if (typeof value === 'string' && value.trim().length > 0) {
        return value;
      }
    }
  }

  return null;
}

function FlowRunExpandedRow({ flowId }: { flowId: string }) {
  const {
    data: flow,
    isLoading,
    error,
    refetch,
  } = useFlowRun(flowId, { enabled: true });

  if (isLoading && !flow) {
    return (
      <div className="flex items-center justify-center py-6">
        <LoadingSpinner size="md" text="Loading flow details..." />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load flow details."
        details={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }

  if (!flow) {
    return (
      <div className="py-6 text-sm text-gray-500">Flow details unavailable.</div>
    );
  }

  const unitId = deriveUnitId(flow);

  return (
    <div className="space-y-4 rounded-md border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-700">Progress:</span>
            <span>{formatPercentage(flow.progress_percentage)}</span>
            <span className="text-gray-400">·</span>
            <span>
              Step {flow.step_progress} / {flow.total_steps ?? '?'}
            </span>
          </div>
          {flow.current_step && (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
              Current step: {flow.current_step}
            </span>
          )}
          {flow.arq_task_id && (
            <Link
              href={`/tasks?taskId=${flow.arq_task_id}`}
              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-500"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              View task
            </Link>
          )}
          {unitId && (
            <Link
              href={`/units/${unitId}`}
              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-500"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7l9-4 9 4-9 4-9-4zm0 6l9 4 9-4" />
              </svg>
              View unit
            </Link>
          )}
        </div>
        <ReloadButton onReload={() => refetch()} isLoading={isLoading} label="Reload flow" />
      </div>

      <FlowStepsList steps={flow.steps} flowId={flow.id} />
    </div>
  );
}

export function FlowRunsList() {
  const filters = useFlowFilters();
  const { setFlowFilters } = useAdminStore();

  const { data, isLoading, error, refetch } = useFlowRuns(filters);
  const [expandedFlows, setExpandedFlows] = useState<Set<string>>(new Set());

  const toggleExpanded = (flowId: string) => {
    setExpandedFlows((current) => {
      const next = new Set(current);
      if (next.has(flowId)) {
        next.delete(flowId);
      } else {
        next.add(flowId);
      }
      return next;
    });
  };

  const handlePageChange = (newPage: number) => {
    setFlowFilters({ page: newPage });
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setFlowFilters({ page: 1, page_size: newPageSize });
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading flow runs..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load flow runs. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  const flows = data?.flows || [];
  const totalCount = data?.total_count || 0;
  const currentPage = data?.page || 1;
  const pageSize = data?.page_size || 10;
  const hasNext = data?.has_next || false;
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6">
      {/* Header with pagination info and reload */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-gray-700">
            Showing {flows.length} of {totalCount} flow runs
          </p>
          <ReloadButton onReload={() => refetch()} isLoading={isLoading} />
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

      {/* Flow runs table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {flows.length === 0 ? (
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
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No flow runs</h3>
            <p className="mt-1 text-sm text-gray-500">
              No flow runs have been executed yet.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Flow Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Steps
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {flows.map((flow) => {
                  const isExpanded = expandedFlows.has(flow.id);
                  return (
                    <Fragment key={flow.id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-3">
                            <button
                              type="button"
                              onClick={() => toggleExpanded(flow.id)}
                              className="rounded-full border border-gray-200 p-1 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
                              aria-label={isExpanded ? 'Collapse flow run details' : 'Expand flow run details'}
                            >
                              <svg
                                className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : 'rotate-0'}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </button>
                            <div>
                              <div className="text-sm font-medium text-gray-900">{flow.flow_name}</div>
                              <div className="text-sm text-gray-500">{flow.execution_mode}</div>
                            </div>
                          </div>
                        </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {flow.user_id ? (
                        <Link href={`/users/${flow.user_id}`} className="text-blue-600 hover:text-blue-900">
                          {flow.user_id}
                        </Link>
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={flow.status} size="sm" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(flow.started_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatExecutionTime(flow.execution_time_ms)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {flow.step_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatTokens(flow.total_tokens)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCost(flow.total_cost)}
                    </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link href={`/flows/${flow.id}`} className="text-blue-600 hover:text-blue-900">
                            View details
                          </Link>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={9} className="px-6 pb-6 pt-2">
                            <FlowRunExpandedRow flowId={flow.id} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!hasNext}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="text-sm text-gray-500">
            Total: {totalCount} flow runs
          </div>
        </div>
      )}
    </div>
  );
}
