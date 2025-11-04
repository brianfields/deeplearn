/**
 * Conversations List Component
 *
 * Displays a paginated list of conversations (learning coach and teaching assistant) with expandable detail rows.
 */

'use client';

import Link from 'next/link';
import { useConversations } from '../../queries';
import { useAdminStore, useConversationFilters } from '../../store';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ReloadButton } from '../shared/ReloadButton';
import { StatusBadge } from '../shared/StatusBadge';
import { ExpandableTable, type ExpandableTableColumn } from '../shared/ExpandableTable';
import { ConversationDetails } from './ConversationDetails';
import { formatDate } from '@/lib/utils';
import type { ConversationSummary } from '../../models';

function ConversationTypeBadge({ type }: { type: string }): JSX.Element {
  const isCoach = type === 'learning_coach';
  const label = isCoach ? 'Coach' : 'Assistant';
  const bgColor = isCoach ? 'bg-blue-100' : 'bg-purple-100';
  const textColor = isCoach ? 'text-blue-800' : 'text-purple-800';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${bgColor} ${textColor}`}>
      {label}
    </span>
  );
}

export function ConversationsList(): JSX.Element {
  const filters = useConversationFilters();
  const { setConversationFilters } = useAdminStore();
  const { data, isLoading, error, refetch } = useConversations(filters);

  const conversations = data?.conversations ?? [];
  const totalCount = data?.total_count ?? 0;
  const currentPage = data?.page ?? filters.page ?? 1;
  const pageSize = data?.page_size ?? filters.page_size ?? 50;
  const hasNext = data?.has_next ?? false;
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(totalCount / pageSize)) : 1;

  const handlePageChange = (newPage: number) => {
    if (newPage < 1) return;
    setConversationFilters({ page: newPage });
  };

  const handlePageSizeChange = (newSize: number) => {
    setConversationFilters({ page: 1, page_size: newSize });
  };

  const emptyIcon = (
    <svg
      className="h-12 w-12 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 10h.01M12 10h.01M16 10h.01M9 16h6m2 5H7a2 2 0 01-2-2V7a2 2 0 012-2h2l1-2h4l1 2h2a2 2 0 012 2v12a2 2 0 01-2 2z"
      />
    </svg>
  );

  const columns: ExpandableTableColumn<ConversationSummary>[] = [
    {
      key: 'title',
      label: 'Title',
      render: (conversation) => {
        const title = conversation.title ?? conversation.metadata.topic ?? 'Untitled conversation';
        return (
          <div>
            <div className="text-sm font-medium text-gray-900">{title}</div>
            {conversation.metadata.topic && (
              <div className="text-xs text-gray-500">Topic: {conversation.metadata.topic}</div>
            )}
          </div>
        );
      },
    },
    {
      key: 'type',
      label: 'Type',
      render: (conversation) => <ConversationTypeBadge type={conversation.conversation_type} />,
    },
    {
      key: 'user',
      label: 'User',
      render: (conversation) => (
        conversation.user_id ? (
          <Link
            href={`/users/${conversation.user_id}`}
            className="text-blue-600 hover:text-blue-500"
          >
            {conversation.user_id}
          </Link>
        ) : (
          <span className="text-gray-500">—</span>
        )
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (conversation) => <StatusBadge status={conversation.status} size="sm" />,
    },
    {
      key: 'message_count',
      label: 'Messages',
      render: (conversation) => conversation.message_count,
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (conversation) => formatDate(conversation.created_at),
    },
    {
      key: 'last_message_at',
      label: 'Last message',
      render: (conversation) => formatDate(conversation.last_message_at),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-700">
          <span>
            Showing {conversations.length} of {totalCount} conversations
          </span>
          <ReloadButton onReload={() => refetch()} isLoading={isLoading} />
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-700">
          <label htmlFor="conversation-page-size">Per page:</label>
          <select
            id="conversation-page-size"
            value={pageSize}
            onChange={(event) => handlePageSizeChange(Number(event.target.value))}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      <ExpandableTable
        data={conversations}
        columns={columns}
        getRowId={(conversation) => conversation.id}
        renderExpandedContent={(conversation) => (
          <ConversationDetails
            conversationId={conversation.id}
            summary={conversation}
          />
        )}
        isLoading={isLoading && conversations.length === 0}
        error={error}
        emptyMessage="Conversations will appear here once they are started by learners."
        emptyIcon={emptyIcon}
        onRetry={() => refetch()}
      />

      {totalPages > 1 && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!hasNext}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="text-sm text-gray-500">Total: {totalCount} conversations</div>
        </div>
      )}
    </div>
  );
}
