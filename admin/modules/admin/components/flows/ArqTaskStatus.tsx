/**
 * ARQ Task Status Component
 *
 * Displays ARQ task information for flows that are running in ARQ mode.
 * Shows task status, queue position, and links to queue monitoring.
 */

'use client';

import Link from 'next/link';
import { useFlowTaskStatus } from '../../queries';
import { StatusBadge } from '../shared/StatusBadge';

interface ArqTaskStatusProps {
  flowId: string;
  executionMode: string;
  flowStatus: string;
}

export function ArqTaskStatus({ flowId, executionMode, flowStatus }: ArqTaskStatusProps) {
  const { data: taskStatus, isLoading } = useFlowTaskStatus(flowId);

  // Only show for ARQ flows
  if (executionMode !== 'arq') {
    return null;
  }

  // Don't show while loading unless we already have task data
  if (isLoading && !taskStatus) {
    return (
      <div className="text-xs text-gray-400">
        Checking queue status...
      </div>
    );
  }

  // No task found - might be completed or not yet queued
  if (!taskStatus) {
    return (
      <div className="text-xs text-gray-500">
        No active queue task
      </div>
    );
  }

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

  const getExecutionTime = () => {
    if (taskStatus.status === 'completed' && taskStatus.started_at && taskStatus.completed_at) {
      return taskStatus.completed_at.getTime() - taskStatus.started_at.getTime();
    }
    if (taskStatus.status === 'running' && taskStatus.started_at) {
      return new Date().getTime() - taskStatus.started_at.getTime();
    }
    return null;
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return null;
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const executionTime = getExecutionTime();

  return (
    <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-xs font-medium text-blue-700">
            ARQ Task:
          </div>
          <StatusBadge 
            status={taskStatus.status}
            variant={getTaskStatusVariant(taskStatus.status)}
            size="sm"
          />
          <div className="text-xs text-gray-600">
            Queue: {taskStatus.queue_name}
          </div>
        </div>
        <Link 
          href={`/queue`}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          View in Queue →
        </Link>
      </div>
      
      <div className="mt-2 grid grid-cols-2 gap-4 text-xs">
        <div>
          <span className="text-gray-500">Task ID:</span>
          <span className="ml-1 font-mono text-gray-700">
            {taskStatus.task_id.substring(0, 12)}...
          </span>
        </div>
        <div>
          <span className="text-gray-500">Submitted:</span>
          <span className="ml-1 text-gray-700">
            {formatTimeAgo(taskStatus.submitted_at)}
          </span>
        </div>
        {taskStatus.started_at && (
          <div>
            <span className="text-gray-500">Started:</span>
            <span className="ml-1 text-gray-700">
              {formatTimeAgo(taskStatus.started_at)}
            </span>
          </div>
        )}
        {executionTime && (
          <div>
            <span className="text-gray-500">Runtime:</span>
            <span className="ml-1 text-gray-700">
              {formatDuration(executionTime)}
            </span>
          </div>
        )}
        {taskStatus.retry_count > 0 && (
          <div>
            <span className="text-gray-500">Retries:</span>
            <span className="ml-1 text-orange-600 font-medium">
              {taskStatus.retry_count}
            </span>
          </div>
        )}
        {taskStatus.priority > 0 && (
          <div>
            <span className="text-gray-500">Priority:</span>
            <span className="ml-1 text-blue-600 font-medium">
              {taskStatus.priority}
            </span>
          </div>
        )}
      </div>
      
      {taskStatus.error_message && (
        <div className="mt-2 p-2 bg-red-50 rounded border border-red-200">
          <div className="text-xs font-medium text-red-700">Error:</div>
          <div className="text-xs text-red-600 mt-1">
            {taskStatus.error_message}
          </div>
        </div>
      )}
    </div>
  );
}