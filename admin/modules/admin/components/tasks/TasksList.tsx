'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useTasks } from '../../queries';
import { DetailViewTable, type DetailViewTableColumn } from '../shared/DetailViewTable';
import { StatusBadge } from '../shared/StatusBadge';
import { formatDate, formatExecutionTime } from '@/lib/utils';
import type { TaskStatus } from '../../models';

function computeDuration(task: TaskStatus): number | null {
  if (task.started_at && task.completed_at) {
    return task.completed_at.getTime() - task.started_at.getTime();
  }
  if (task.started_at && task.status === 'running') {
    return Date.now() - task.started_at.getTime();
  }
  return null;
}

function getAssociatedEntity(task: TaskStatus): { href: string; label: string } | null {
  if (task.unit_id) {
    return { href: `/units/${task.unit_id}`, label: `Unit ${task.unit_id}` };
  }
  if (task.flow_run_id) {
    return { href: `/flows/${task.flow_run_id}`, label: 'Flow run' };
  }
  if (task.flow_name) {
    return { href: '#', label: task.flow_name };
  }
  return null;
}

export function TasksList(): JSX.Element {
  const { data: allTasks, isLoading, error, refetch } = useTasks();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const PAGE_SIZE_OPTIONS = [10, 25, 50];

  // Client-side pagination
  const { tasks, totalCount, totalPages } = useMemo(() => {
    const sorted = (allTasks ?? []).slice().sort((a, b) => b.submitted_at.getTime() - a.submitted_at.getTime());
    const total = sorted.length;
    const pages = Math.max(1, Math.ceil(total / pageSize));
    const startIdx = (page - 1) * pageSize;
    const endIdx = startIdx + pageSize;
    const paginated = sorted.slice(startIdx, endIdx);

    return {
      tasks: paginated,
      totalCount: total,
      totalPages: pages,
    };
  }, [allTasks, page, pageSize]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reset to first page when changing page size
  };

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
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );

  const columns: DetailViewTableColumn<TaskStatus>[] = [
    {
      key: 'task_id',
      label: 'Task ID',
      render: (task) => (
        <span className="font-mono text-sm text-gray-900">
          {task.task_id.slice(0, 10)}…
        </span>
      ),
    },
    {
      key: 'task_type',
      label: 'Task Type',
      render: (task) => (
        <span className="text-sm text-gray-700">
          {task.task_type || task.flow_name || '—'}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (task) => <StatusBadge status={task.status} size="sm" />,
    },
    {
      key: 'started_at',
      label: 'Started',
      render: (task) => (
        <span className="text-sm text-gray-700">
          {task.started_at ? formatDate(task.started_at) : '—'}
        </span>
      ),
    },
    {
      key: 'duration',
      label: 'Duration',
      render: (task) => {
        const duration = computeDuration(task);
        return (
          <span className="text-sm text-gray-700">
            {duration !== null ? formatExecutionTime(duration) : '—'}
          </span>
        );
      },
    },
    {
      key: 'associated',
      label: 'Associated',
      render: (task) => {
        const associated = getAssociatedEntity(task);
        return associated ? (
          <Link
            href={associated.href}
            className={`text-sm ${
              associated.href === '#' ? 'pointer-events-none text-gray-500' : 'text-blue-600 hover:text-blue-500'
            }`}
            onClick={(e) => {
              if (associated.href === '#') {
                e.preventDefault();
              }
            }}
          >
            {associated.label}
          </Link>
        ) : (
          <span className="text-sm text-gray-500">—</span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <DetailViewTable
        data={tasks}
        columns={columns}
        getRowId={(task) => task.task_id}
        getDetailHref={(task) => `/tasks/${task.task_id}`}
        isLoading={isLoading}
        error={error}
        emptyMessage="No background tasks found."
        emptyIcon={emptyIcon}
        onRetry={() => refetch()}
        pagination={{
          currentPage: page,
          totalPages,
          totalCount,
          pageSize,
          hasNext: page < totalPages,
        }}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        pageOptions={PAGE_SIZE_OPTIONS}
      />
    </div>
  );
}
