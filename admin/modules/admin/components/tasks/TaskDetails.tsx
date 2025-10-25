'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import { useTask, useTaskFlowRuns } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { ReloadButton } from '../shared/ReloadButton';
import {
  formatDate,
  formatExecutionTime,
  formatPercentage,
  formatTokens,
  formatCost,
} from '@/lib/utils';

interface TaskDetailsProps {
  taskId: string | null;
}

export function TaskDetails({ taskId }: TaskDetailsProps) {
  const {
    data: task,
    isLoading: taskLoading,
    error: taskError,
    refetch: refetchTask,
  } = useTask(taskId);
  const {
    data: flowRuns,
    isLoading: flowsLoading,
    error: flowsError,
    refetch: refetchFlows,
  } = useTaskFlowRuns(taskId);

  const isLoading = taskLoading && !task;

  const handleReload = () => {
    void refetchTask();
    void refetchFlows();
  };

  if (!taskId) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
        Select a task to see details.
      </div>
    );
  }

  if (isLoading) {
    return <LoadingSpinner size="md" text="Loading task…" />;
  }

  if (taskError) {
    return (
      <ErrorMessage
        message="Failed to load task details."
        details={taskError instanceof Error ? taskError.message : undefined}
        onRetry={() => handleReload()}
      />
    );
  }

  if (!task) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
        Task not found.
      </div>
    );
  }

  const duration = task.started_at
    ? formatExecutionTime(
        task.completed_at
          ? task.completed_at.getTime() - task.started_at.getTime()
          : Date.now() - task.started_at.getTime(),
      )
    : '—';

  const flowSummary = useMemo(() => flowRuns ?? [], [flowRuns]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Task Details</h2>
          <p className="mt-1 text-sm text-gray-500">ARQ background task metadata and linked flow runs.</p>
        </div>
        <ReloadButton onReload={handleReload} isLoading={taskLoading || flowsLoading} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase text-gray-500">Task ID</p>
              <p className="font-mono text-sm text-gray-900">{task.task_id}</p>
            </div>
            <StatusBadge status={task.status} size="sm" />
          </div>
          <dl className="mt-4 space-y-2 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <dt>Queue</dt>
              <dd>{task.queue_name}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Priority</dt>
              <dd>{task.priority}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Worker</dt>
              <dd>{task.worker_id ?? '—'}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Submitted</dt>
              <dd>{formatDate(task.submitted_at)}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Started</dt>
              <dd>{task.started_at ? formatDate(task.started_at) : '—'}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Completed</dt>
              <dd>{task.completed_at ? formatDate(task.completed_at) : '—'}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Duration</dt>
              <dd>{duration}</dd>
            </div>
            {typeof task.progress_percentage === 'number' && (
              <div className="flex items-center justify-between">
                <dt>Progress</dt>
                <dd>{formatPercentage(task.progress_percentage)}</dd>
              </div>
            )}
            {task.current_step && (
              <div className="flex items-center justify-between">
                <dt>Current step</dt>
                <dd>{task.current_step}</dd>
              </div>
            )}
            {task.retry_count > 0 && (
              <div className="flex items-center justify-between">
                <dt>Retries</dt>
                <dd>{task.retry_count}</dd>
              </div>
            )}
          </dl>
          {task.error_message && (
            <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {task.error_message}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900">Associated entity</h3>
          <dl className="mt-3 space-y-2 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <dt>Flow name</dt>
              <dd>{task.flow_name ?? '—'}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Flow run</dt>
              <dd>
                {task.flow_run_id ? (
                  <Link href={`/flows/${task.flow_run_id}`} className="text-blue-600 hover:text-blue-500">
                    {task.flow_run_id}
                  </Link>
                ) : (
                  '—'
                )}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Unit</dt>
              <dd>
                {task.unit_id ? (
                  <Link href={`/units/${task.unit_id}`} className="text-blue-600 hover:text-blue-500">
                    {task.unit_id}
                  </Link>
                ) : (
                  '—'
                )}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>User</dt>
              <dd>{task.user_id ?? '—'}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Result payload</dt>
              <dd>{task.result ? 'Available' : 'Pending'}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h3 className="text-sm font-semibold text-gray-900">Flow runs</h3>
          <ReloadButton onReload={() => refetchFlows()} isLoading={flowsLoading} label="Reload flows" />
        </div>
        {flowsLoading && !flowRuns && <LoadingSpinner size="sm" text="Loading flow runs…" />}
        {flowsError && (
          <ErrorMessage
            message="Failed to load flow runs for this task."
            details={flowsError instanceof Error ? flowsError.message : undefined}
            onRetry={() => refetchFlows()}
          />
        )}
        {!flowsLoading && flowSummary.length === 0 && (
          <div className="px-4 py-6 text-sm text-gray-500">No flow runs linked to this task yet.</div>
        )}
        {flowSummary.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Flow</th>
                  <th className="px-4 py-3 text-left font-medium">Status</th>
                  <th className="px-4 py-3 text-left font-medium">Started</th>
                  <th className="px-4 py-3 text-left font-medium">Duration</th>
                  <th className="px-4 py-3 text-left font-medium">Tokens</th>
                  <th className="px-4 py-3 text-left font-medium">Cost</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white text-sm text-gray-700">
                {flowSummary.map((flow) => (
                  <tr key={flow.id}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{flow.flow_name}</div>
                      <div className="text-xs text-gray-500">{flow.execution_mode}</div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={flow.status} size="sm" />
                    </td>
                    <td className="px-4 py-3">{formatDate(flow.started_at)}</td>
                    <td className="px-4 py-3">{formatExecutionTime(flow.execution_time_ms)}</td>
                    <td className="px-4 py-3">{formatTokens(flow.total_tokens)}</td>
                    <td className="px-4 py-3">{formatCost(flow.total_cost)}</td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/flows/${flow.id}`} className="text-blue-600 hover:text-blue-500">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
