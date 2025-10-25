/**
 * Conversations List Page
 *
 * Presents the admin view of learning coach conversations.
 */

import { ConversationsList } from '@/modules/admin/components/conversations/ConversationsList';

export default function ConversationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Conversations</h1>
        <p className="mt-2 text-gray-600">
          Review learning coach conversations and inspect message transcripts.
        </p>
      </div>

      <ConversationsList />
    </div>
  );
}
