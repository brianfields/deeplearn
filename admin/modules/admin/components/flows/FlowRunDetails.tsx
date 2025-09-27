/**
 * Flow Run Details Component
 *
 * Shows detailed information about a specific flow run and its steps.
 */

'use client';

import Link from 'next/link';
import { useFlowRun } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { JSONViewer } from '../shared/JSONViewer';
import { FlowStepsList } from './FlowStepsList';
import { ArqTaskStatus } from './ArqTaskStatus';
import {
  formatDate,
  formatExecutionTime,
  formatCost,
  formatTokens,
  formatPercentage
} from '@/lib/utils';

interface FlowRunDetailsProps {
  flowId: string;
}

export function FlowRunDetails({ flowId }: FlowRunDetailsProps) {
  const { data: flow, isLoading, error, refetch } = useFlowRun(flowId);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading flow details..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load flow details. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  if (!flow) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Flow not found</h3>
        <p className="mt-2 text-gray-600">
          The requested flow run could not be found.
        </p>
        <Link
          href="/flows"
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Back to flows
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Link
              href="/flows"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back to flows
            </Link>
          </div>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">
            {flow.flow_name}
          </h1>
          <div className="mt-2 flex items-center space-x-4">
            <StatusBadge status={flow.status} />
            <span className="text-sm text-gray-500">
              {flow.execution_mode} execution
            </span>
            {flow.user_id && (
              <Link
                href={`/users/${flow.user_id}`}
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                User {flow.user_id}
              </Link>
            )}
          </div>
        </div>

        {/* Reload Button */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>{isLoading ? 'Reloading...' : 'Reload Flow'}</span>
          </button>

          {/* Auto-refresh indicator for running flows */}
          {flow.status === 'running' && (
            <div className="flex items-center space-x-1 text-xs text-blue-600">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
              <span>Running</span>
            </div>
          )}
        </div>
      </div>

      {/* ARQ Task Status */}
      <ArqTaskStatus 
        flowId={flow.id}
        executionMode={flow.execution_mode}
        flowStatus={flow.status}
      />

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
              <p className="text-sm font-medium text-gray-600">Duration</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatExecutionTime(flow.execution_time_ms)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Progress</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatPercentage(flow.progress_percentage)}
              </p>
              <p className="text-xs text-gray-500">
                {flow.step_progress} / {flow.total_steps || '?'} steps
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Tokens</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatTokens(flow.total_tokens)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Cost</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCost(flow.total_cost)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Timeline</h2>
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Created:</span>
            <span className="text-sm font-medium text-gray-900">
              {formatDate(flow.created_at)}
            </span>
          </div>
          {flow.started_at && (
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Started:</span>
              <span className="text-sm font-medium text-gray-900">
                {formatDate(flow.started_at)}
              </span>
            </div>
          )}
          {flow.completed_at && (
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Completed:</span>
              <span className="text-sm font-medium text-gray-900">
                {formatDate(flow.completed_at)}
              </span>
            </div>
          )}
          {flow.last_heartbeat && (
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Last heartbeat:</span>
              <span className="text-sm font-medium text-gray-900">
                {formatDate(flow.last_heartbeat)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {flow.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-red-800">Error</h3>
          <p className="mt-1 text-sm text-red-700">{flow.error_message}</p>
        </div>
      )}

      {/* Input/Output Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <JSONViewer
            data={flow.inputs}
            title="Input Data"
            maxHeight="max-h-96"
          />
        </div>

        {flow.outputs && (
          <div className="bg-white rounded-lg shadow p-6">
            <JSONViewer
              data={flow.outputs}
              title="Output Data"
              maxHeight="max-h-96"
            />
          </div>
        )}
      </div>

      {/* Flow Steps */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Flow Steps</h2>
        </div>
        <FlowStepsList steps={flow.steps} flowId={flow.id} />
      </div>
    </div>
  );
}
