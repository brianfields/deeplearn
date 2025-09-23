/**
 * Queue Statistics Chart Component
 *
 * Displays queue performance metrics in visual format:
 * - Task throughput over time
 * - Queue depth trends
 * - Worker utilization
 * - Processing time distribution
 */

'use client';

import type { QueueStats } from '../../models';
import { LoadingSpinner } from '../shared/LoadingSpinner';

interface QueueStatsChartProps {
  queueStats: QueueStats[];
  isLoading: boolean;
}

interface StatDisplayProps {
  title: string;
  value: number | string;
  subtitle?: string;
  format?: 'number' | 'percent' | 'time' | 'text';
}

function StatDisplay({ title, value, subtitle, format = 'number' }: StatDisplayProps) {
  const formatValue = (val: number | string, fmt: string) => {
    if (typeof val === 'string') return val;
    
    switch (fmt) {
      case 'percent':
        return `${(val * 100).toFixed(1)}%`;
      case 'time':
        if (val < 1000) return `${val}ms`;
        return `${(val / 1000).toFixed(1)}s`;
      case 'number':
      default:
        return val.toLocaleString();
    }
  };

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <div className="text-lg font-semibold text-gray-900">
        {formatValue(value, format)}
      </div>
      <div className="text-sm font-medium text-gray-600">{title}</div>
      {subtitle && (
        <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
      )}
    </div>
  );
}

interface QueueStatsTableProps {
  queueStats: QueueStats[];
}

function QueueStatsTable({ queueStats }: QueueStatsTableProps) {
  if (queueStats.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No queue statistics available
      </div>
    );
  }

  const formatTime = (ms: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatDate = (date: Date | null) => {
    if (!date) return '-';
    return date.toLocaleString();
  };

  const getWorkerUtilization = (stats: QueueStats) => {
    if (stats.workers_count === 0) return 0;
    return stats.workers_busy / stats.workers_count;
  };

  const getSuccessRate = (stats: QueueStats) => {
    const total = stats.completed_count + stats.failed_count;
    if (total === 0) return 1;
    return stats.completed_count / total;
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatDisplay 
          title="Total Processed"
          value={queueStats.reduce((sum, s) => sum + s.total_processed, 0)}
        />
        <StatDisplay 
          title="Success Rate"
          value={queueStats.length > 0 
            ? queueStats.reduce((sum, s) => sum + getSuccessRate(s), 0) / queueStats.length 
            : 0
          }
          format="percent"
        />
        <StatDisplay 
          title="Avg Processing Time"
          value={queueStats.length > 0
            ? queueStats.reduce((sum, s) => sum + (s.avg_processing_time_ms || 0), 0) / queueStats.length
            : 0
          }
          format="time"
        />
        <StatDisplay 
          title="Worker Utilization"
          value={queueStats.length > 0
            ? queueStats.reduce((sum, s) => sum + getWorkerUtilization(s), 0) / queueStats.length
            : 0
          }
          format="percent"
        />
      </div>

      {/* Detailed Queue Stats Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Queue Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Queue
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Load
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Workers
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  History
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {queueStats.map((stats) => (
                <tr key={stats.queue_name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {stats.queue_name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      <div>Pending: {stats.pending_count}</div>
                      <div>Running: {stats.running_count}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      <div>{stats.workers_busy}/{stats.workers_count} busy</div>
                      <div className="text-xs text-gray-500">
                        {(getWorkerUtilization(stats) * 100).toFixed(0)}% utilization
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      <div>Avg: {formatTime(stats.avg_processing_time_ms)}</div>
                      <div className="text-xs text-gray-500">
                        {(getSuccessRate(stats) * 100).toFixed(1)}% success
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      <div>Total: {stats.total_processed.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">
                        Failed: {stats.failed_count}
                      </div>
                      {stats.oldest_pending_task && (
                        <div className="text-xs text-orange-600">
                          Oldest: {formatDate(stats.oldest_pending_task)}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export function QueueStatsChart({ queueStats, isLoading }: QueueStatsChartProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return <QueueStatsTable queueStats={queueStats} />;
}