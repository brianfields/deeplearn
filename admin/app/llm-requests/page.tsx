/**
 * LLM Requests List Page
 *
 * Shows list of LLM requests with basic information.
 */

'use client';

import { LLMRequestsList } from '@/modules/admin/components/llm-requests/LLMRequestsList';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';
import { useLLMRequests } from '@/modules/admin/queries';
import { useLLMRequestFilters } from '@/modules/admin/store';

export default function LLMRequestsPage() {
  const filters = useLLMRequestFilters();
  const { refetch, isLoading } = useLLMRequests(filters);

  return (
    <div className="space-y-6">
      <PageHeader
        title="LLM Requests"
        description="View detailed information about LLM requests and their responses"
        onReload={() => refetch()}
        isReloading={isLoading}
      />

      <LLMRequestsList />
    </div>
  );
}
