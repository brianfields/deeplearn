/**
 * Flow Runs List Component
 *
 * Displays paginated list of flow runs with basic controls.
 */

'use client';

import Link from 'next/link';
import { useFlowRun, useFlowRuns } from '../../queries';
import { useFlowFilters, useAdminStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { ReloadButton } from '../shared/ReloadButton';
import { ExpandableTable, type ExpandableTableColumn } from '../shared/ExpandableTable';
import { FlowStepsList } from './FlowStepsList';
import {
  formatDate,
  formatExecutionTime,
  formatCost,
  formatTokens,
  formatPercentage,
} from '@/lib/utils';
import type { FlowRunDetails, FlowRunSummary } from '../../models';
import { LoadingSpinner } from '../shared/LoadingSpinner';

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

function FlowRunExpandedRow({ flowId }: { flowId: string }): JSX.Element {
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
      <div className="py-6 text-sm text-red-500">
        Failed to load flow details. {error instanceof Error ? error.message : ''}
      </div>
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

export function FlowRunsList(): JSX.Element {
  const filters = useFlowFilters();
  const { setFlowFilters } = useAdminStore();

  const { data, isLoading, error, refetch } = useFlowRuns(filters);

  const handlePageChange = (newPage: number) => {
    setFlowFilters({ page: newPage });
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setFlowFilters({ page: 1, page_size: newPageSize });
  };

  const flows = data?.flows || [];
  const totalCount = data?.total_count || 0;
  const currentPage = data?.page || 1;
  const pageSize = data?.page_size || 10;
  const hasNext = data?.has_next || false;

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
        d="M13 10V3L4 14h7v7l9-11h-7z"
      />
    </svg>
  );

  const columns: ExpandableTableColumn<FlowRunSummary>[] = [
    {
      key: 'flow_name',
      label: 'Flow Name',
      render: (flow) => (
        <div>
          <div className="text-sm font-medium text-gray-900">{flow.flow_name}</div>
          <div className="text-sm text-gray-500">{flow.execution_mode}</div>
        </div>
      ),
    },
    {
      key: 'user_id',
      label: 'User',
      render: (flow) =>
        flow.user_id ? (
          <Link href={`/users/${flow.user_id}`} className="text-blue-600 hover:text-blue-900">
            {flow.user_id}
          </Link>
        ) : (
          <span className="text-gray-500">—</span>
        ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (flow) => <StatusBadge status={flow.status} size="sm" />,
    },
    {
      key: 'started_at',
      label: 'Started',
      render: (flow) => formatDate(flow.started_at),
    },
    {
      key: 'duration',
      label: 'Duration',
      render: (flow) => formatExecutionTime(flow.execution_time_ms),
    },
    {
      key: 'steps',
      label: 'Steps',
      render: (flow) => flow.step_count ?? '—',
    },
    {
      key: 'tokens',
      label: 'Tokens',
      render: (flow) => formatTokens(flow.total_tokens),
    },
    {
      key: 'cost',
      label: 'Cost',
      render: (flow) => formatCost(flow.total_cost),
    },
  ];

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
      <ExpandableTable
        data={flows}
        columns={columns}
        getRowId={(flow) => flow.id}
        renderExpandedContent={(flow) => <FlowRunExpandedRow flowId={flow.id} />}
        isLoading={isLoading}
        error={error}
        emptyMessage="No flow runs have been executed yet."
        emptyIcon={emptyIcon}
        onRetry={() => refetch()}
      />

      {/* Pagination */}
      {totalCount > pageSize && (
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
              Page {currentPage} of {Math.ceil(totalCount / pageSize)}
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
