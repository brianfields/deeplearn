/**
 * LLM Requests List Page
 *
 * Shows list of LLM requests with basic information.
 */

import { LLMRequestsList } from '@/modules/admin/components/llm-requests/LLMRequestsList';

export default function LLMRequestsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">LLM Requests</h1>
        <p className="text-gray-600 mt-2">
          View detailed information about LLM requests and their responses
        </p>
      </div>

      <LLMRequestsList />
    </div>
  );
}
