/**
 * Conversations List Page
 *
 * Presents the admin view of all conversations (learning coach and teaching assistant).
 */

'use client';

import { ConversationsList } from '@/modules/admin/components/conversations/ConversationsList';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';
import { useConversations } from '@/modules/admin/queries';
import { useConversationFilters } from '@/modules/admin/store';

export default function ConversationsPage() {
  const filters = useConversationFilters();
  const { refetch, isLoading } = useConversations(filters);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Conversations"
        description="Review learning coach and teaching assistant conversations, and inspect message transcripts."
        onReload={() => refetch()}
        isReloading={isLoading}
      />

      <ConversationsList />
    </div>
  );
}
