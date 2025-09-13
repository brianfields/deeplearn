/**
 * Flow Run Details Page
 *
 * Shows detailed information about a specific flow run and its steps.
 */

import { FlowRunDetails } from '@/modules/admin/components/flows/FlowRunDetails';

interface FlowDetailsPageProps {
  params: { id: string };
}

export default function FlowDetailsPage({ params }: FlowDetailsPageProps) {
  return (
    <div className="space-y-6">
      <FlowRunDetails flowId={params.id} />
    </div>
  );
}
