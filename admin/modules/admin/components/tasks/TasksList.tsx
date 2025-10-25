'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import { useTasks } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { ReloadButton } from '../shared/ReloadButton';
import { formatDate, formatExecutionTime } from '@/lib/utils';
import type { TaskStatus } from '../../models';

interface TasksListProps {
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  limit?: number;
}

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

export function TasksList({ selectedTaskId, onSelectTask, limit = 100 }: TasksListProps) {
  const {
    data: tasks,
    isLoading,
    error,
    refetch,
  } = useTasks(limit);

  const sortedTasks = useMemo(() => {
    return (tasks ?? []).slice().sort((a, b) => b.submitted_at.getTime() - a.submitted_at.getTime());
  }, [tasks]);

  if (isLoading && !tasks) {
    return <LoadingSpinner size="md" text="Loading tasks…" />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load tasks."
        details={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }

  if (!sortedTasks.length) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Tasks</h2>
          <ReloadButton onReload={() => refetch()} isLoading={isLoading} />
        </div>
        <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
          No background tasks found.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Tasks</h2>
        <ReloadButton onReload={() => refetch()} isLoading={isLoading} />
      </div>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Task ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Task Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Started</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Duration</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Associated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {sortedTasks.map((task) => {
              const isSelected = task.task_id === selectedTaskId;
              const duration = computeDuration(task);
              const associated = getAssociatedEntity(task);

              return (
                <tr
                  key={task.task_id}
                  onClick={() => onSelectTask(task.task_id)}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">
                    {task.task_id.slice(0, 10)}…
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {task.task_type || task.flow_name || '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    <StatusBadge status={task.status} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {task.started_at ? formatDate(task.started_at) : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {duration !== null ? formatExecutionTime(duration) : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-blue-600">
                    {associated ? (
                      <Link
                        href={associated.href}
                        className={`hover:text-blue-500 ${associated.href === '#' ? 'pointer-events-none text-gray-500 hover:text-gray-500' : ''}`}
                        onClick={(event) => {
                          if (associated.href === '#') {
                            event.preventDefault();
                          }
                        }}
                      >
                        {associated.label}
                      </Link>
                    ) : (
                      <span className="text-gray-500">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
