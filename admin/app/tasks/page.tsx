/**
 * Tasks Page
 *
 * Main view of background tasks with queue summary and stats.
 */

'use client';

import { useQueryClient } from '@tanstack/react-query';
import { TasksList } from '@/modules/admin/components/tasks/TasksList';
import { useQueueStats, useQueueStatus, useWorkers, useTasks } from '@/modules/admin/queries';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';

export default function TasksPage(): JSX.Element {
  const queryClient = useQueryClient();

  const {
    data: queueStatus,
    isLoading: statusLoading,
    refetch: refetchStatus,
  } = useQueueStatus();
  const {
    data: queueStats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQueueStats();
  const {
    data: workers,
    isLoading: workersLoading,
    refetch: refetchWorkers,
  } = useWorkers();
  const {
    refetch: refetchTasks,
    isLoading: tasksLoading,
  } = useTasks();

  const handleReloadAll = () => {
    void refetchStatus();
    void refetchStats();
    void refetchWorkers();
    void refetchTasks();
  };

  const isReloading = statusLoading || statsLoading || workersLoading || tasksLoading;
  const status = queueStatus?.[0];
  const stats = queueStats?.[0];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Tasks"
        description="Monitor ARQ background tasks, worker activity, and linked flow runs."
        onReload={handleReloadAll}
        isReloading={isReloading}
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase text-gray-500">Queue status</p>
          {statusLoading && !status ? (
            <LoadingSpinner size="sm" />
          ) : status ? (
            <div className="mt-2 flex items-center gap-3">
              <StatusBadge status={status.status} size="sm" />
              <span className="text-sm text-gray-700">{status.queue_name}</span>
            </div>
          ) : (
            <p className="mt-2 text-sm text-gray-500">No data</p>
          )}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase text-gray-500">Task metrics</p>
          {statsLoading && !stats ? (
            <LoadingSpinner size="sm" />
          ) : stats ? (
            <dl className="mt-2 space-y-1 text-sm text-gray-700">
              <div className="flex items-center justify-between">
                <dt>Pending</dt>
                <dd>{stats.pending_count}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt>Running</dt>
                <dd>{stats.running_count}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt>Completed</dt>
                <dd>{stats.completed_count}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt>Failed</dt>
                <dd>{stats.failed_count}</dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-sm text-gray-500">No data</p>
          )}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase text-gray-500">Workers online</p>
          {workersLoading && !workers ? (
            <LoadingSpinner size="sm" />
          ) : workers ? (
            <p className="mt-2 text-sm text-gray-700">{workers.length}</p>
          ) : (
            <p className="mt-2 text-sm text-gray-500">No data</p>
          )}
        </div>
      </div>

      <TasksList />
    </div>
  );
}
