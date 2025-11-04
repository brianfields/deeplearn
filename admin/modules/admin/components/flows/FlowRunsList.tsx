/**
 * Flow Runs List Component
 *
 * Displays paginated list of flow runs with links to detail pages.
 */

'use client';

import Link from 'next/link';
import { useFlowRuns } from '../../queries';
import { useFlowFilters, useAdminStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { DetailViewTable, type DetailViewTableColumn } from '../shared/DetailViewTable';
import {
  formatDate,
  formatExecutionTime,
  formatCost,
  formatTokens,
} from '@/lib/utils';
import type { FlowRunSummary } from '../../models';

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
  const totalPages = Math.ceil(totalCount / pageSize);

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
        d="M13 10V3L4 14h7v7l9-11h-7z"
      />
    </svg>
  );

  const columns: DetailViewTableColumn<FlowRunSummary>[] = [
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
          <Link href={`/users/${flow.user_id}`} className="text-blue-600 hover:text-blue-900" onClick={(e) => e.stopPropagation()}>
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

      {/* Flow runs table */}
      <DetailViewTable
        data={flows}
        columns={columns}
        getRowId={(flow) => flow.id}
        getDetailHref={(flow) => `/flows/${flow.id}`}
        isLoading={isLoading}
        error={error}
        emptyMessage="No flow runs have been executed yet."
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
