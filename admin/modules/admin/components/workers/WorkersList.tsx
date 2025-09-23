/**
 * Workers List Component
 *
 * Displays detailed list of individual workers with their
 * status, current tasks, and performance metrics.
 */

'use client';

import { useState } from 'react';
import type { WorkerHealth } from '../../models';
import { StatusBadge } from '../shared/StatusBadge';
import { LoadingSpinner } from '../shared/LoadingSpinner';

interface WorkersListProps {
  workers: WorkerHealth[];
  isLoading: boolean;
}

interface WorkersTableProps {
  workers: WorkerHealth[];
}

function WorkersTable({ workers }: WorkersTableProps) {
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

  const formatUptime = (startDate: Date) => {
    const now = new Date();
    const diff = now.getTime() - startDate.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return `${days}d ${remainingHours}h`;
    }
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'busy': return 'info';
      case 'unhealthy': return 'warning';
      case 'offline': return 'error';
      default: return 'secondary';
    }
  };

  const getHeartbeatHealth = (lastHeartbeat: Date) => {
    const now = new Date();
    const diff = now.getTime() - lastHeartbeat.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 2) return 'healthy';
    if (minutes < 5) return 'warning';
    return 'critical';
  };

  const getHeartbeatColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-orange-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (workers.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No workers found
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Worker
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Current Task
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Performance
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Health
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Uptime
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {workers.map((worker) => {
            const heartbeatHealth = getHeartbeatHealth(worker.last_heartbeat);
            
            return (
              <tr key={worker.worker_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {worker.worker_id}
                    </div>
                    <div className="text-sm text-gray-500">
                      Queue: {worker.queue_name}
                    </div>
                    {worker.version && (
                      <div className="text-xs text-gray-400">
                        v{worker.version}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge 
                    status={worker.status}
                    variant={getStatusVariant(worker.status)}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {worker.current_task_id ? (
                      <>
                        <div className="font-medium">
                          {worker.current_task_id.substring(0, 8)}...
                        </div>
                        <div className="text-xs text-gray-500">
                          In progress
                        </div>
                      </>
                    ) : (
                      <span className="text-gray-400">Idle</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    <div>{worker.tasks_completed} completed</div>
                    <div className="text-xs text-gray-500">
                      {worker.tasks_completed > 0 && worker.started_at && (
                        <>
                          {(worker.tasks_completed / 
                            ((new Date().getTime() - worker.started_at.getTime()) / (1000 * 60 * 60))
                          ).toFixed(1)} tasks/hr
                        </>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm">
                    <div className={getHeartbeatColor(heartbeatHealth)}>
                      {formatTimeAgo(worker.last_heartbeat)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Last heartbeat
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatUptime(worker.started_at)}
                  </div>
                  <div className="text-xs text-gray-500">
                    Since {worker.started_at.toLocaleTimeString()}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function WorkersList({ workers, isLoading }: WorkersListProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [queueFilter, setQueueFilter] = useState<string>('all');

  // Get unique queues
  const uniqueQueues = Array.from(new Set(workers.map(w => w.queue_name)));

  // Filter workers
  const filteredWorkers = workers.filter(worker => {
    const statusMatch = statusFilter === 'all' || worker.status === statusFilter;
    const queueMatch = queueFilter === 'all' || worker.queue_name === queueFilter;
    return statusMatch && queueMatch;
  });

  const statusCounts = {
    all: workers.length,
    healthy: workers.filter(w => w.status === 'healthy').length,
    busy: workers.filter(w => w.status === 'busy').length,
    unhealthy: workers.filter(w => w.status === 'unhealthy').length,
    offline: workers.filter(w => w.status === 'offline').length,
  };

  const statusOptions = [
    { value: 'all', label: 'All Workers', count: statusCounts.all },
    { value: 'healthy', label: 'Healthy', count: statusCounts.healthy },
    { value: 'busy', label: 'Busy', count: statusCounts.busy },
    { value: 'unhealthy', label: 'Unhealthy', count: statusCounts.unhealthy },
    { value: 'offline', label: 'Offline', count: statusCounts.offline },
  ];

  const queueOptions = [
    { value: 'all', label: 'All Queues', count: workers.length },
    ...uniqueQueues.map(queue => ({
      value: queue,
      label: queue,
      count: workers.filter(w => w.queue_name === queue).length,
    })),
  ];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        {/* Status Filter */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700 self-center">Status:</span>
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

        {/* Queue Filter */}
        {uniqueQueues.length > 1 && (
          <div className="flex flex-wrap gap-2">
            <span className="text-sm font-medium text-gray-700 self-center">Queue:</span>
            {queueOptions.map(option => (
              <button
                key={option.value}
                onClick={() => setQueueFilter(option.value)}
                className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${queueFilter === option.value
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                {option.label}
                <span className="ml-1 text-xs">({option.count})</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Workers Table */}
      <div className="bg-white shadow rounded-lg">
        {isLoading ? (
          <div className="flex justify-center items-center h-32">
            <LoadingSpinner />
          </div>
        ) : (
          <WorkersTable workers={filteredWorkers} />
        )}
      </div>
    </div>
  );
}