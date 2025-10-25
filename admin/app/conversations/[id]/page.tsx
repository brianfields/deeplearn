/**
 * Conversation Detail Page
 *
 * Renders a full-page view of a single learning coach conversation.
 */

import Link from 'next/link';
import { ConversationDetails } from '@/modules/admin/components/conversations/ConversationDetails';

interface ConversationDetailPageProps {
  params: { id: string };
}

export default function ConversationDetailPage({ params }: ConversationDetailPageProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <Link href="/conversations" className="text-sm text-gray-500 hover:text-gray-700">
          ← Back to conversations
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Conversation {params.id}</h1>
        <p className="text-gray-600">
          Inspect the full transcript, message metadata, and associated resources.
        </p>
      </div>

      <ConversationDetails conversationId={params.id} />
    </div>
  );
}
