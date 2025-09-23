/**
 * Workers Monitoring Component
 *
 * Displays real-time worker status including:
 * - Worker health overview
 * - Individual worker details
 * - Performance metrics
 * - Current task assignments
 */

'use client';

import { useState } from 'react';
import { useWorkers, useQueueHealth } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { WorkersOverview } from './WorkersOverview';
import { WorkersList } from './WorkersList';
import { WorkersPerformance } from './WorkersPerformance';

interface WorkersMonitoringProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function WorkersMonitoring({
  autoRefresh = true,
  refreshInterval = 15000,
}: WorkersMonitoringProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'workers' | 'performance'>('overview');

  // Fetch data with auto-refresh
  const {
    data: workers,
    isLoading: workersLoading,
    error: workersError,
  } = useWorkers();

  const {
    data: queueHealth,
    isLoading: healthLoading,
    error: healthError,
  } = useQueueHealth();

  const isLoading = workersLoading || healthLoading;
  const hasError = workersError || healthError;

  if (isLoading && !workers && !queueHealth) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (hasError) {
    return (
      <ErrorMessage 
        message="Failed to load worker monitoring data"
        details={workersError?.message || healthError?.message}
      />
    );
  }

  // Calculate worker stats
  const totalWorkers = workers?.length || 0;
  const healthyWorkers = workers?.filter(w => w.status === 'healthy').length || 0;
  const busyWorkers = workers?.filter(w => w.status === 'busy').length || 0;
  const unhealthyWorkers = workers?.filter(w => ['unhealthy', 'offline'].includes(w.status)).length || 0;

  const tabs = [
    { 
      id: 'overview' as const, 
      label: 'Overview',
      count: totalWorkers,
    },
    { 
      id: 'workers' as const, 
      label: 'Workers',
      count: totalWorkers,
    },
    { 
      id: 'performance' as const, 
      label: 'Performance',
      count: healthyWorkers + busyWorkers,
    },
  ];

  // Overall system health
  const systemHealthy = queueHealth?.status === 'healthy' && unhealthyWorkers === 0;
  const systemStatus = systemHealthy ? 'healthy' : 'degraded';
  const systemBadgeVariant = systemHealthy ? 'success' : 'warning';

  return (
    <div className="space-y-6">
      {/* System Status Indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            System Status:
          </div>
          <StatusBadge 
            status={systemStatus}
            variant={systemBadgeVariant}
          />
          <div className="text-sm text-gray-600">
            {healthyWorkers}/{totalWorkers} workers healthy
            {busyWorkers > 0 && `, ${busyWorkers} busy`}
          </div>
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
          <WorkersOverview 
            workers={workers || []}
            queueHealth={queueHealth}
          />
        )}

        {selectedTab === 'workers' && (
          <WorkersList 
            workers={workers || []}
            isLoading={workersLoading}
          />
        )}

        {selectedTab === 'performance' && (
          <WorkersPerformance 
            workers={workers || []}
            isLoading={workersLoading}
          />
        )}
      </div>
    </div>
  );
}