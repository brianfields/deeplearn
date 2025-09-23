/**
 * Queue Tasks List Component
 *
 * Displays a table of recent tasks with their status, timing,
 * and basic details. Allows filtering and provides task detail drill-down.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { TaskStatus } from '../../models';
import { StatusBadge } from '../shared/StatusBadge';
import { LoadingSpinner } from '../shared/LoadingSpinner';

interface QueueTasksListProps {
  tasks: TaskStatus[];
  isLoading: boolean;
}

interface TasksTableProps {
  tasks: TaskStatus[];
}

function TasksTable({ tasks }: TasksTableProps) {
  const formatDuration = (ms: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const getExecutionTime = (task: TaskStatus) => {
    if (task.status === 'completed' && task.started_at && task.completed_at) {
      return task.completed_at.getTime() - task.started_at.getTime();
    }
    if (task.status === 'running' && task.started_at) {
      return new Date().getTime() - task.started_at.getTime();
    }
    return null;
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      case 'cancelled': return 'secondary';
      default: return 'secondary';
    }
  };

  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No tasks found
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Task
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Flow
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Queue
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Timing
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Retries
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {tasks.map((task) => (
            <tr key={task.task_id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {task.task_id.substring(0, 8)}...
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatTimeAgo(task.submitted_at)}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusBadge 
                  status={task.status}
                  variant={getStatusVariant(task.status)}
                />
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  {task.flow_name && (
                    <>
                      <div className="text-sm text-gray-900">{task.flow_name}</div>
                      {task.flow_run_id && (
                        <Link 
                          href={`/flows/${task.flow_run_id}`}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          View Flow →
                        </Link>
                      )}
                    </>
                  )}
                  {!task.flow_name && (
                    <span className="text-sm text-gray-500">-</span>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {task.queue_name}
                {task.priority > 0 && (
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    P{task.priority}
                  </span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDuration(getExecutionTime(task))}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <span className={`text-sm ${task.retry_count > 0 ? 'text-orange-600' : 'text-gray-500'}`}>
                    {task.retry_count}
                  </span>
                  {task.error_message && (
                    <div className="ml-2 text-xs text-red-600 truncate max-w-32" title={task.error_message}>
                      {task.error_message}
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function QueueTasksList({ tasks, isLoading }: QueueTasksListProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Filter tasks by status
  const filteredTasks = tasks.filter(task => 
    statusFilter === 'all' || task.status === statusFilter
  );

  const statusCounts = {
    all: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    running: tasks.filter(t => t.status === 'running').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
    cancelled: tasks.filter(t => t.status === 'cancelled').length,
  };

  const statusOptions = [
    { value: 'all', label: 'All Tasks', count: statusCounts.all },
    { value: 'pending', label: 'Pending', count: statusCounts.pending },
    { value: 'running', label: 'Running', count: statusCounts.running },
    { value: 'completed', label: 'Completed', count: statusCounts.completed },
    { value: 'failed', label: 'Failed', count: statusCounts.failed },
    { value: 'cancelled', label: 'Cancelled', count: statusCounts.cancelled },
  ];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {statusOptions.map(option => (
          <button
            key={option.value}
            onClick={() => setStatusFilter(option.value)}
            className={`
              px-3 py-1 rounded-full text-sm font-medium
              ${statusFilter === option.value
                ? 'bg-blue-100 text-blue-700 border border-blue-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            {option.label}
            <span className="ml-1 text-xs">({option.count})</span>
          </button>
        ))}
      </div>

      {/* Tasks Table */}
      <div className="bg-white shadow rounded-lg">
        {isLoading ? (
          <div className="flex justify-center items-center h-32">
            <LoadingSpinner />
          </div>
        ) : (
          <TasksTable tasks={filteredTasks} />
        )}
      </div>
    </div>
  );
}