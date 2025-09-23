/**
 * Queue Monitoring Component
 *
 * Displays real-time task queue status including:
 * - Queue overview cards
 * - Recent tasks list with status
 * - Queue statistics and performance metrics
 */

'use client';

import { useState } from 'react';
import { useQueueStatus, useQueueStats, useQueueTasks } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { QueueOverviewCards } from './QueueOverviewCards';
import { QueueTasksList } from './QueueTasksList';
import { QueueStatsChart } from './QueueStatsChart';

interface QueueMonitoringProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function QueueMonitoring({
  autoRefresh = true,
  refreshInterval = 10000,
}: QueueMonitoringProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'tasks' | 'stats'>('overview');

  // Fetch data with auto-refresh
  const {
    data: queueStatus,
    isLoading: statusLoading,
    error: statusError,
  } = useQueueStatus();

  const {
    data: queueStats,
    isLoading: statsLoading,
    error: statsError,
  } = useQueueStats();

  const {
    data: recentTasks,
    isLoading: tasksLoading,
    error: tasksError,
  } = useQueueTasks(50);

  const isLoading = statusLoading || statsLoading || tasksLoading;
  const hasError = statusError || statsError || tasksError;

  if (isLoading && !queueStatus && !queueStats && !recentTasks) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (hasError) {
    return (
      <ErrorMessage 
        message="Failed to load queue monitoring data"
        details={statusError?.message || statsError?.message || tasksError?.message}
      />
    );
  }

  const tabs = [
    { id: 'overview' as const, label: 'Overview', count: queueStatus?.length || 0 },
    { id: 'tasks' as const, label: 'Recent Tasks', count: recentTasks?.length || 0 },
    { id: 'stats' as const, label: 'Statistics', count: queueStats?.length || 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Status Indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Queue Status:
          </div>
          <StatusBadge 
            status={queueStatus?.[0]?.status || 'unknown'}
            variant={queueStatus?.[0]?.status === 'healthy' ? 'success' : 
                     queueStatus?.[0]?.status === 'degraded' ? 'warning' : 'error'}
          />
        </div>
        {autoRefresh && (
          <div className="text-xs text-gray-400">
            Auto-refreshes every {refreshInterval / 1000}s
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`
                whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
                ${selectedTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {selectedTab === 'overview' && (
          <QueueOverviewCards 
            queueStatus={queueStatus || []}
            queueStats={queueStats || []}
          />
        )}

        {selectedTab === 'tasks' && (
          <QueueTasksList 
            tasks={recentTasks || []}
            isLoading={tasksLoading}
          />
        )}

        {selectedTab === 'stats' && (
          <QueueStatsChart 
            queueStats={queueStats || []}
            isLoading={statsLoading}
          />
        )}
      </div>
    </div>
  );
}