/**
 * LLM Request Details Page
 *
 * Shows detailed information about a specific LLM request.
 */

import { LLMRequestDetails } from '@/modules/admin/components/llm-requests/LLMRequestDetails';

interface LLMRequestDetailsPageProps {
  params: { id: string };
}

export default function LLMRequestDetailsPage({ params }: LLMRequestDetailsPageProps) {
  return (
    <div className="space-y-6">
      <LLMRequestDetails requestId={params.id} />
    </div>
  );
}
