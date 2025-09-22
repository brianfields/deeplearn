/**
 * Workers Overview Component
 *
 * High-level summary of worker status and system health.
 */

'use client';

import type { WorkerHealth } from '../../models';

interface WorkersOverviewProps {
  workers: WorkerHealth[];
  queueHealth: { status: string; details: Record<string, any> } | undefined;
}

interface OverviewCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  color?: 'blue' | 'green' | 'orange' | 'red' | 'gray';
  icon?: string;
}

function OverviewCard({ title, value, subtitle, color = 'blue', icon }: OverviewCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-gray-50 text-gray-700 border-gray-200',
  };

  return (
    <div className={`p-6 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium opacity-75">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs mt-1 opacity-60">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-2xl">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

function WorkerStatusChart({ workers }: { workers: WorkerHealth[] }) {
  const statusCounts = {
    healthy: workers.filter(w => w.status === 'healthy').length,
    busy: workers.filter(w => w.status === 'busy').length,
    unhealthy: workers.filter(w => w.status === 'unhealthy').length,
    offline: workers.filter(w => w.status === 'offline').length,
  };

  const total = workers.length;

  if (total === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No workers detected
      </div>
    );
  }

  const statusLabels = [
    { status: 'healthy', label: 'Healthy', color: 'bg-green-500', count: statusCounts.healthy },
    { status: 'busy', label: 'Busy', color: 'bg-blue-500', count: statusCounts.busy },
    { status: 'unhealthy', label: 'Unhealthy', color: 'bg-orange-500', count: statusCounts.unhealthy },
    { status: 'offline', label: 'Offline', color: 'bg-red-500', count: statusCounts.offline },
  ];

  return (
    <div className="space-y-4">
      {/* Status Bar */}
      <div className="flex rounded-lg overflow-hidden h-4">
        {statusLabels.map(({ status, color, count }) => {
          const percentage = (count / total) * 100;
          return percentage > 0 ? (
            <div
              key={status}
              className={color}
              style={{ width: `${percentage}%` }}
              title={`${count} ${status} workers (${percentage.toFixed(1)}%)`}
            />
          ) : null;
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        {statusLabels.map(({ status, label, color, count }) => (
          <div key={status} className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${color}`} />
            <span className="text-gray-600">{label}</span>
            <span className="font-medium text-gray-900">({count})</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function WorkersOverview({ workers, queueHealth }: WorkersOverviewProps) {
  const totalWorkers = workers.length;
  const healthyWorkers = workers.filter(w => w.status === 'healthy').length;
  const busyWorkers = workers.filter(w => w.status === 'busy').length;
  const activeWorkers = healthyWorkers + busyWorkers;
  const totalTasksCompleted = workers.reduce((sum, w) => sum + w.tasks_completed, 0);

  // Calculate uptime (time since oldest worker started)
  const oldestWorkerStart = workers.length > 0 
    ? Math.min(...workers.map(w => w.started_at.getTime()))
    : null;
  const systemUptimeHours = oldestWorkerStart 
    ? Math.floor((new Date().getTime() - oldestWorkerStart) / (1000 * 60 * 60))
    : 0;

  // Worker efficiency
  const avgTasksPerWorker = totalWorkers > 0 ? totalTasksCompleted / totalWorkers : 0;
  const workerEfficiency = totalWorkers > 0 ? activeWorkers / totalWorkers : 0;

  const cards: OverviewCardProps[] = [
    {
      title: 'Total Workers',
      value: totalWorkers,
      subtitle: `${activeWorkers} active`,
      color: totalWorkers > 0 ? 'blue' : 'gray',
      icon: '👥',
    },
    {
      title: 'System Health',
      value: queueHealth?.status || 'Unknown',
      subtitle: `${Math.round(workerEfficiency * 100)}% efficiency`,
      color: queueHealth?.status === 'healthy' ? 'green' : 'orange',
      icon: queueHealth?.status === 'healthy' ? '✅' : '⚠️',
    },
    {
      title: 'Tasks Completed',
      value: totalTasksCompleted.toLocaleString(),
      subtitle: `${avgTasksPerWorker.toFixed(1)} avg/worker`,
      color: 'green',
      icon: '✨',
    },
    {
      title: 'System Uptime',
      value: systemUptimeHours > 0 ? `${systemUptimeHours}h` : 'Just started',
      subtitle: oldestWorkerStart ? new Date(oldestWorkerStart).toLocaleTimeString() : 'No data',
      color: 'blue',
      icon: '⏱️',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, index) => (
          <OverviewCard key={index} {...card} />
        ))}
      </div>

      {/* Worker Status Distribution */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="mb-4">
          <h3 className="text-lg font-medium text-gray-900">Worker Status Distribution</h3>
          <p className="text-sm text-gray-500">Current status of all workers</p>
        </div>
        <WorkerStatusChart workers={workers} />
      </div>

      {/* System Health Details */}
      {queueHealth?.details && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-900">System Health Details</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(queueHealth.details).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium text-gray-600 capitalize">
                  {key.replace(/_/g, ' ')}
                </div>
                <div className="text-sm text-gray-900 mt-1">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}