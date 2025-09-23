/**
 * Workers Status Page
 *
 * Real-time monitoring of ARQ worker health, status,
 * and performance metrics with auto-refresh.
 */

import { WorkersMonitoring } from '@/modules/admin/components/workers/WorkersMonitoring';

export default function WorkersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Workers</h1>
        <p className="text-gray-600 mt-2">
          Monitor ARQ worker health, performance, and current task assignments
        </p>
      </div>

      <WorkersMonitoring />
    </div>
  );
}