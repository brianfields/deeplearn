/**
 * Conversations List Component
 *
 * Displays a paginated list of conversations (learning coach and teaching assistant) with expandable detail rows.
 */

'use client';

import Link from 'next/link';
import { Fragment, useState } from 'react';
import { useConversations } from '../../queries';
import { useAdminStore, useConversationFilters } from '../../store';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { ReloadButton } from '../shared/ReloadButton';
import { StatusBadge } from '../shared/StatusBadge';
import { ConversationDetails } from './ConversationDetails';
import { formatDate } from '@/lib/utils';

function ConversationTypeBadge({ type }: { type: string }) {
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

export function ConversationsList() {
  const filters = useConversationFilters();
  const { setConversationFilters } = useAdminStore();
  const { data, isLoading, error, refetch } = useConversations(filters);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const conversations = data?.conversations ?? [];
  const totalCount = data?.total_count ?? 0;
  const currentPage = data?.page ?? filters.page ?? 1;
  const pageSize = data?.page_size ?? filters.page_size ?? 50;
  const hasNext = data?.has_next ?? false;
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(totalCount / pageSize)) : 1;

  const toggleExpanded = (conversationId: string) => {
    setExpandedRows((current) => {
      const next = new Set(current);
      if (next.has(conversationId)) {
        next.delete(conversationId);
      } else {
        next.add(conversationId);
      }
      return next;
    });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage < 1) return;
    setConversationFilters({ page: newPage });
  };

  const handlePageSizeChange = (newSize: number) => {
    setConversationFilters({ page: 1, page_size: newSize });
  };

  if (isLoading && conversations.length === 0) {
    return <LoadingSpinner size="lg" text="Loading conversations..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load conversations. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

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

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {conversations.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
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
            <h3 className="mt-2 text-sm font-medium text-gray-900">No conversations</h3>
            <p className="mt-1 text-sm text-gray-500">
              Conversations will appear here once they are started by learners.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Messages
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last message
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {conversations.map((conversation) => {
                  const isExpanded = expandedRows.has(conversation.id);
                  const title = conversation.title ?? conversation.metadata.topic ?? 'Untitled conversation';

                  return (
                    <Fragment key={conversation.id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <button
                              type="button"
                              onClick={() => toggleExpanded(conversation.id)}
                              className="rounded-full border border-gray-200 p-1 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
                              aria-label={isExpanded ? 'Collapse conversation details' : 'Expand conversation details'}
                            >
                              <svg
                                className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : 'rotate-0'}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </button>
                            <div>
                              <div className="text-sm font-medium text-gray-900">{title}</div>
                              {conversation.metadata.topic && (
                                <div className="text-xs text-gray-500">Topic: {conversation.metadata.topic}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <ConversationTypeBadge type={conversation.conversation_type} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {conversation.user_id ? (
                            <Link
                              href={`/users/${conversation.user_id}`}
                              className="text-blue-600 hover:text-blue-500"
                            >
                              {conversation.user_id}
                            </Link>
                          ) : (
                            <span className="text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={conversation.status} size="sm" />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {conversation.message_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(conversation.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(conversation.last_message_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link href={`/conversations/${conversation.id}`} className="text-blue-600 hover:text-blue-500">
                            View details
                          </Link>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={8} className="px-6 pb-6 pt-2">
                            <ConversationDetails
                              conversationId={conversation.id}
                              summary={conversation}
                            />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
