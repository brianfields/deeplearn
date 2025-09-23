/**
 * Queue Overview Cards Component
 *
 * Displays high-level queue metrics in card format:
 * - Pending tasks
 * - Running tasks
 * - Worker count
 * - Processing rate
 */

'use client';

import type { QueueStatus, QueueStats } from '../../models';

interface QueueOverviewCardsProps {
  queueStatus: QueueStatus[];
  queueStats: QueueStats[];
}

interface MetricCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'blue' | 'green' | 'orange' | 'red' | 'gray';
}

function MetricCard({ title, value, subtitle, trend, color = 'blue' }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-gray-50 text-gray-700 border-gray-200',
  };

  const trendIcons = {
    up: '↗️',
    down: '↘️',
    neutral: '→',
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
        {trend && (
          <div className="text-lg">
            {trendIcons[trend]}
          </div>
        )}
      </div>
    </div>
  );
}

export function QueueOverviewCards({ queueStatus, queueStats }: QueueOverviewCardsProps) {
  // Aggregate data across all queues
  const totalPending = queueStatus.reduce((sum, q) => sum + q.pending_count, 0);
  const totalRunning = queueStatus.reduce((sum, q) => sum + q.running_count, 0);
  const totalWorkers = queueStatus.reduce((sum, q) => sum + q.worker_count, 0);
  
  const totalProcessed = queueStats.reduce((sum, s) => sum + s.total_processed, 0);
  const avgProcessingTime = queueStats.length > 0
    ? queueStats.reduce((sum, s) => sum + (s.avg_processing_time_ms || 0), 0) / queueStats.length
    : 0;

  const oldestPendingMinutes = Math.max(
    ...queueStatus.map(q => q.oldest_pending_minutes || 0)
  );

  // Determine overall health
  const hasUnhealthyQueue = queueStatus.some(q => q.status !== 'healthy');
  const healthColor = hasUnhealthyQueue ? 'red' : 'green';
  const healthStatus = hasUnhealthyQueue ? 'Issues Detected' : 'Healthy';

  const cards: MetricCardProps[] = [
    {
      title: 'Queue Health',
      value: healthStatus,
      subtitle: `${queueStatus.length} queue${queueStatus.length !== 1 ? 's' : ''} monitored`,
      color: healthColor,
    },
    {
      title: 'Pending Tasks',
      value: totalPending,
      subtitle: oldestPendingMinutes > 0 ? `Oldest: ${oldestPendingMinutes}m ago` : 'No pending tasks',
      color: totalPending > 10 ? 'orange' : 'blue',
    },
    {
      title: 'Running Tasks',
      value: totalRunning,
      subtitle: `${totalWorkers} worker${totalWorkers !== 1 ? 's' : ''} active`,
      color: totalRunning > 0 ? 'green' : 'gray',
    },
    {
      title: 'Total Processed',
      value: totalProcessed.toLocaleString(),
      subtitle: avgProcessingTime > 0 
        ? `Avg: ${Math.round(avgProcessingTime)}ms` 
        : 'No timing data',
      color: 'blue',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <MetricCard key={index} {...card} />
      ))}
    </div>
  );
}