/**
 * Dashboard Overview Component
 *
 * Main dashboard showing quick stats and recent activity.
 */

'use client';

import Link from 'next/link';
import { useFlowRuns } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { formatDate, formatExecutionTime, formatCost } from '@/lib/utils';

export function DashboardOverview() {
  const { data: flowRuns, isLoading, error, refetch } = useFlowRuns({ page: 1, page_size: 5 });

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load dashboard data. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  const recentFlows = flowRuns?.flows || [];
  const totalFlows = flowRuns?.total_count || 0;

  // Calculate quick stats
  const completedFlows = recentFlows.filter(f => f.status === 'completed').length;
  const runningFlows = recentFlows.filter(f => f.status === 'running').length;
  const failedFlows = recentFlows.filter(f => f.status === 'failed').length;

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Flows</p>
              <p className="text-2xl font-semibold text-gray-900">{totalFlows}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-semibold text-gray-900">{completedFlows}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Running</p>
              <p className="text-2xl font-semibold text-gray-900">{runningFlows}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Failed</p>
              <p className="text-2xl font-semibold text-gray-900">{failedFlows}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Flow Runs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Recent Flow Runs</h2>
            <Link
              href="/flows"
              className="text-sm font-medium text-blue-600 hover:text-blue-500"
            >
              View all
            </Link>
          </div>
        </div>

        {recentFlows.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <p className="text-gray-500">No flow runs found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {recentFlows.map((flow) => (
              <div key={flow.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <Link
                        href={`/flows/${flow.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-500 truncate"
                      >
                        {flow.flow_name}
                      </Link>
                      <StatusBadge status={flow.status} size="sm" />
                    </div>
                    <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                      <span>Started: {formatDate(flow.started_at)}</span>
                      {flow.execution_time_ms && (
                        <span>Duration: {formatExecutionTime(flow.execution_time_ms)}</span>
                      )}
                      <span>Cost: {formatCost(flow.total_cost)}</span>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <Link
                      href={`/flows/${flow.id}`}
                      className="text-sm text-gray-400 hover:text-gray-600"
                    >
                      View details →
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
