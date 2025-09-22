/**
 * Workers Performance Component
 *
 * Displays worker performance metrics and analytics including:
 * - Task completion rates
 * - Worker efficiency comparisons
 * - Performance trends
 */

'use client';

import type { WorkerHealth } from '../../models';
import { LoadingSpinner } from '../shared/LoadingSpinner';

interface WorkersPerformanceProps {
  workers: WorkerHealth[];
  isLoading: boolean;
}

interface PerformanceMetricProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
}

function PerformanceMetric({ title, value, subtitle, trend }: PerformanceMetricProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  const trendIcons = {
    up: '↗️',
    down: '↘️',
    neutral: '→',
  };

  return (
    <div className="bg-white p-4 rounded-lg border">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {trend && (
          <div className={`text-lg ${trendColors[trend]}`}>
            {trendIcons[trend]}
          </div>
        )}
      </div>
    </div>
  );
}

function WorkerPerformanceTable({ workers }: { workers: WorkerHealth[] }) {
  // Calculate performance metrics for each worker
  const workerMetrics = workers.map(worker => {
    const uptime = new Date().getTime() - worker.started_at.getTime();
    const uptimeHours = uptime / (1000 * 60 * 60);
    const tasksPerHour = uptimeHours > 0 ? worker.tasks_completed / uptimeHours : 0;
    
    return {
      ...worker,
      uptime,
      uptimeHours,
      tasksPerHour,
    };
  });

  // Sort by performance (tasks per hour)
  const sortedWorkers = [...workerMetrics].sort((a, b) => b.tasksPerHour - a.tasksPerHour);

  const formatUptime = (ms: number) => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return `${days}d ${remainingHours}h`;
    }
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (workers.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No workers available for performance analysis
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Rank
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Worker
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tasks/Hour
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Total Tasks
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Uptime
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Efficiency
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedWorkers.map((worker, index) => {
            const isTopPerformer = index < 3 && worker.tasksPerHour > 0;
            const efficiency = worker.uptimeHours > 0 
              ? Math.min((worker.tasks_completed / worker.uptimeHours) / 10, 1) // Normalize to 0-1 scale
              : 0;
            
            return (
              <tr 
                key={worker.worker_id} 
                className={`hover:bg-gray-50 ${isTopPerformer ? 'bg-green-50' : ''}`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className={`
                      font-bold text-sm
                      ${index === 0 ? 'text-yellow-600' : 
                        index === 1 ? 'text-gray-500' : 
                        index === 2 ? 'text-orange-600' : 'text-gray-400'}
                    `}>
                      #{index + 1}
                    </span>
                    {isTopPerformer && (
                      <span className="ml-2 text-lg">
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {worker.worker_id}
                    </div>
                    <div className="text-sm text-gray-500">
                      {worker.queue_name}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-semibold text-gray-900">
                    {worker.tasksPerHour.toFixed(2)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {worker.tasks_completed}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatUptime(worker.uptime)}
                  </div>
                  <div className="text-xs text-gray-500">
                    Since {worker.started_at.toLocaleTimeString()}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`
                    inline-flex px-2 py-1 text-xs font-semibold rounded-full
                    ${worker.status === 'healthy' ? 'bg-green-100 text-green-800' :
                      worker.status === 'busy' ? 'bg-blue-100 text-blue-800' :
                      worker.status === 'unhealthy' ? 'bg-orange-100 text-orange-800' :
                      'bg-red-100 text-red-800'}
                  `}>
                    {worker.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${efficiency * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">
                      {(efficiency * 100).toFixed(0)}%
                    </span>
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

export function WorkersPerformance({ workers, isLoading }: WorkersPerformanceProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  // Calculate aggregate performance metrics
  const totalTasks = workers.reduce((sum, w) => sum + w.tasks_completed, 0);
  const activeWorkers = workers.filter(w => ['healthy', 'busy'].includes(w.status)).length;
  
  // Average tasks per hour across all workers
  const avgTasksPerHour = workers.length > 0 
    ? workers.reduce((sum, w) => {
        const uptime = new Date().getTime() - w.started_at.getTime();
        const hours = uptime / (1000 * 60 * 60);
        return sum + (hours > 0 ? w.tasks_completed / hours : 0);
      }, 0) / workers.length
    : 0;

  // System uptime (average of all workers)
  const avgUptime = workers.length > 0
    ? workers.reduce((sum, w) => sum + (new Date().getTime() - w.started_at.getTime()), 0) / workers.length
    : 0;

  const formatSystemUptime = (ms: number) => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    return `${hours}h`;
  };

  // Top performer
  const topPerformer = workers.length > 0
    ? workers.reduce((best, current) => {
        const currentRate = current.tasks_completed / ((new Date().getTime() - current.started_at.getTime()) / (1000 * 60 * 60));
        const bestRate = best.tasks_completed / ((new Date().getTime() - best.started_at.getTime()) / (1000 * 60 * 60));
        return currentRate > bestRate ? current : best;
      })
    : null;

  return (
    <div className="space-y-6">
      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PerformanceMetric
          title="Avg Tasks/Hour"
          value={avgTasksPerHour.toFixed(2)}
          subtitle="System-wide average"
        />
        <PerformanceMetric
          title="Total Tasks"
          value={totalTasks.toLocaleString()}
          subtitle="All workers combined"
        />
        <PerformanceMetric
          title="Active Workers"
          value={`${activeWorkers}/${workers.length}`}
          subtitle={`${((activeWorkers / (workers.length || 1)) * 100).toFixed(0)}% online`}
        />
        <PerformanceMetric
          title="Avg System Uptime"
          value={formatSystemUptime(avgUptime)}
          subtitle="Average worker uptime"
        />
      </div>

      {/* Top Performer Highlight */}
      {topPerformer && topPerformer.tasks_completed > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-lg border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">🏆 Top Performer</h3>
              <p className="text-gray-600">
                <span className="font-medium">{topPerformer.worker_id}</span> has completed{' '}
                <span className="font-bold text-green-600">{topPerformer.tasks_completed}</span> tasks
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">
                {(topPerformer.tasks_completed / ((new Date().getTime() - topPerformer.started_at.getTime()) / (1000 * 60 * 60))).toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">tasks/hour</div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Performance Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Worker Performance Ranking</h3>
          <p className="text-sm text-gray-500">
            Workers ranked by task completion rate and efficiency
          </p>
        </div>
        <WorkerPerformanceTable workers={workers} />
      </div>
    </div>
  );
}