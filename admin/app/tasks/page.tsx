/**
 * Tasks Page
 *
 * Unified view of background tasks, workers, and related flow runs.
 */

'use client';

import { useState } from 'react';
import { TasksList } from '@/modules/admin/components/tasks/TasksList';
import { TaskDetails } from '@/modules/admin/components/tasks/TaskDetails';
import { useQueueStats, useQueueStatus, useWorkers } from '@/modules/admin/queries';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ReloadButton } from '@/modules/admin/components/shared/ReloadButton';

export default function TasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

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

  const handleReloadSummary = () => {
    void refetchStatus();
    void refetchStats();
    void refetchWorkers();
  };

  const status = queueStatus?.[0];
  const stats = queueStats?.[0];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tasks</h1>
          <p className="mt-2 text-gray-600">
            Monitor ARQ background tasks, worker activity, and linked flow runs.
          </p>
        </div>
        <ReloadButton
          onReload={handleReloadSummary}
          isLoading={statusLoading || statsLoading || workersLoading}
          label="Reload summary"
        />
      </div>

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

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <TasksList selectedTaskId={selectedTaskId} onSelectTask={setSelectedTaskId} />
        <TaskDetails taskId={selectedTaskId} />
      </div>
    </div>
  );
}
