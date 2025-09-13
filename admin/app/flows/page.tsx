/**
 * Flow Runs List Page
 *
 * Shows paginated list of flow runs with basic filtering.
 */

import { FlowRunsList } from '@/modules/admin/components/flows/FlowRunsList';

export default function FlowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Flow Runs</h1>
        <p className="text-gray-600 mt-2">
          Monitor flow executions and drill down into step details
        </p>
      </div>

      <FlowRunsList />
    </div>
  );
}
