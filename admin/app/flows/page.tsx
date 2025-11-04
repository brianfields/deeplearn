/**
 * Flow Runs List Page
 *
 * Shows paginated list of flow runs with basic filtering.
 */

'use client';

import { FlowRunsList } from '@/modules/admin/components/flows/FlowRunsList';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';
import { useFlowRuns } from '@/modules/admin/queries';
import { useFlowFilters } from '@/modules/admin/store';

export default function FlowsPage() {
  const filters = useFlowFilters();
  const { refetch, isLoading } = useFlowRuns(filters);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Flow Runs"
        description="Monitor flow executions and drill down into step details"
        onReload={() => refetch()}
        isReloading={isLoading}
      />

      <FlowRunsList />
    </div>
  );
}
