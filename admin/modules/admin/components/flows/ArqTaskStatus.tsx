/**
 * ARQ Task Status Component
 *
 * Displays ARQ task information for flows that are running in ARQ mode.
 * Shows task status, queue position, and links to queue monitoring.
 */

'use client';

import Link from 'next/link';
import { useTask } from '../../queries';
import { StatusBadge } from '../shared/StatusBadge';
import { ReloadButton } from '../shared/ReloadButton';

interface ArqTaskStatusProps {
  taskId: string | null;
  executionMode: string;
}

export function ArqTaskStatus({ taskId, executionMode }: ArqTaskStatusProps) {
  if (executionMode !== 'arq') {
    return null;
  }

  if (!taskId) {
    return (
      <div className="text-xs text-gray-500">No task ID recorded for this flow.</div>
    );
  }

  const {
    data: taskStatus,
    isLoading,
    error,
    refetch,
  } = useTask(taskId);

  const getTaskStatusVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      case 'cancelled': return 'secondary';
      default: return 'secondary';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const executionDuration = (() => {
    if (!taskStatus?.started_at) {
      return null;
    }
    const end = taskStatus.completed_at ?? new Date();
    return end.getTime() - taskStatus.started_at.getTime();
  })();

  return (
    <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-xs font-medium text-blue-700">Background task:</div>
          <StatusBadge
            status={taskStatus?.status ?? 'unknown'}
            variant={taskStatus ? getTaskStatusVariant(taskStatus.status) : 'secondary'}
            size="sm"
          />
          {taskStatus?.queue_name && (
            <div className="text-xs text-gray-600">Queue: {taskStatus.queue_name}</div>
          )}
          {taskStatus?.worker_id && (
            <div className="text-xs text-gray-600">Worker: {taskStatus.worker_id}</div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ReloadButton onReload={() => refetch()} isLoading={isLoading} label="Refresh" />
          <Link href={`/tasks?taskId=${taskId}`} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
            View in Tasks →
          </Link>
        </div>
      </div>

      {isLoading && !taskStatus && !error && (
        <div className="mt-3 text-xs text-gray-400">Loading task details…</div>
      )}

      {error && (
        <div className="mt-3 text-xs text-red-500">Failed to load task status.</div>
      )}

      {taskStatus && (
        <div className="mt-2 grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
          <div>
            <span className="text-gray-500">Task ID:</span>
            <span className="ml-1 font-mono text-gray-700">{taskStatus.task_id.slice(0, 12)}…</span>
          </div>
          <div>
            <span className="text-gray-500">Submitted:</span>
            <span className="ml-1 text-gray-700">{formatTimeAgo(taskStatus.submitted_at)}</span>
          </div>
          {taskStatus.started_at && (
            <div>
              <span className="text-gray-500">Started:</span>
              <span className="ml-1 text-gray-700">{formatTimeAgo(taskStatus.started_at)}</span>
            </div>
          )}
          {executionDuration && (
            <div>
              <span className="text-gray-500">Runtime:</span>
              <span className="ml-1 text-gray-700">{formatDuration(executionDuration)}</span>
            </div>
          )}
          {taskStatus.current_step && (
            <div>
              <span className="text-gray-500">Current step:</span>
              <span className="ml-1 text-gray-700">{taskStatus.current_step}</span>
            </div>
          )}
          {typeof taskStatus.progress_percentage === 'number' && (
            <div>
              <span className="text-gray-500">Progress:</span>
              <span className="ml-1 text-gray-700">{taskStatus.progress_percentage.toFixed(1)}%</span>
            </div>
          )}
          {taskStatus.retry_count > 0 && (
            <div>
              <span className="text-gray-500">Retries:</span>
              <span className="ml-1 text-orange-600 font-medium">{taskStatus.retry_count}</span>
            </div>
          )}
          <div>
            <span className="text-gray-500">Priority:</span>
            <span className="ml-1 text-gray-700">{taskStatus.priority}</span>
          </div>
        </div>
      )}

      {taskStatus?.error_message && (
        <div className="mt-2 rounded border border-red-200 bg-red-50 p-2">
          <div className="text-xs font-medium text-red-700">Error:</div>
          <div className="mt-1 text-xs text-red-600">{taskStatus.error_message}</div>
        </div>
      )}
    </div>
  );
}

function formatDuration(ms: number | null) {
  if (!ms) {
    return '—';
  }
  if (ms < 1000) {
    return `${ms}ms`;
  }
  if (ms < 60_000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  if (minutes < 60) {
    return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}