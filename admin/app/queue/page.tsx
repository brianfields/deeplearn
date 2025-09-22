/**
 * Queue Monitoring Page
 *
 * Real-time monitoring of ARQ task queue status, recent tasks,
 * and queue statistics with auto-refresh.
 */

import { QueueMonitoring } from '@/modules/admin/components/queue/QueueMonitoring';

export default function QueuePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Task Queue</h1>
        <p className="text-gray-600 mt-2">
          Monitor ARQ task queue status, worker health, and task execution
        </p>
      </div>

      <QueueMonitoring />
    </div>
  );
}