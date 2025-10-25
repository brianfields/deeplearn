/**
 * Conversation Details Component
 *
 * Fetches and renders an expanded view of a learning coach conversation.
 */

'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import { useConversation } from '../../queries';
import type { ConversationSummary } from '../../models';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { ReloadButton } from '../shared/ReloadButton';
import { StatusBadge } from '../shared/StatusBadge';
import { MessageTranscript } from './MessageTranscript';
import { formatDate, formatJSON } from '@/lib/utils';

interface ConversationDetailsProps {
  conversationId: string;
  summary?: ConversationSummary;
}

function resolveValue<T>(...candidates: Array<T | null | undefined>): T | null {
  for (const candidate of candidates) {
    if (candidate !== undefined && candidate !== null) {
      return candidate;
    }
  }
  return null;
}

export function ConversationDetails({ conversationId, summary }: ConversationDetailsProps) {
  const {
    data: conversation,
    isLoading,
    error,
    refetch,
  } = useConversation(conversationId, { enabled: !!conversationId });

  const resolvedMetadata = useMemo(() => {
    return conversation?.metadata ?? summary?.metadata ?? {};
  }, [conversation?.metadata, summary?.metadata]);

  if (isLoading && !conversation) {
    return <LoadingSpinner size="md" text="Loading conversation details..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load conversation details."
        details={error instanceof Error ? error.message : undefined}
        onRetry={() => refetch()}
      />
    );
  }

  if (!conversation) {
    return <p className="text-sm text-gray-500">Conversation details unavailable.</p>;
  }

  const title = resolveValue<string | undefined>(
    summary?.title ?? undefined,
    (resolvedMetadata.title as string | undefined),
    (resolvedMetadata.topic as string | undefined)
  ) ?? `Conversation ${conversation.conversation_id}`;

  const status = resolveValue<string>(
    summary?.status,
    (resolvedMetadata.status as string | undefined)
  ) ?? 'unknown';

  const messageCount = summary?.message_count ?? conversation.messages.length;
  const createdAt = resolveValue<string | Date>(
    summary?.created_at,
    resolvedMetadata.created_at as string | Date | undefined,
    resolvedMetadata.createdAt as string | Date | undefined
  );
  const updatedAt = resolveValue<string | Date>(
    summary?.updated_at,
    resolvedMetadata.updated_at as string | Date | undefined,
    resolvedMetadata.updatedAt as string | Date | undefined
  );
  const lastMessageAt = resolveValue<string | Date>(
    summary?.last_message_at,
    resolvedMetadata.last_message_at as string | Date | undefined,
    resolvedMetadata.lastMessageAt as string | Date | undefined,
    conversation.messages[conversation.messages.length - 1]?.created_at
  );

  const userId = resolveValue<number | string>(
    summary?.user_id ?? undefined,
    resolvedMetadata.user_id as number | string | undefined,
    resolvedMetadata.userId as number | string | undefined,
    resolvedMetadata.user?.id as number | string | undefined
  );

  const topic = resolvedMetadata.topic as string | undefined;
  const costEstimateRaw = resolvedMetadata.cost_estimate;
  const costEstimate = typeof costEstimateRaw === 'number' ? costEstimateRaw : null;

  return (
    <div className="space-y-6 rounded-md border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            <StatusBadge status={status} size="sm" />
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
            <span>Messages: {messageCount}</span>
            <span>Conversation ID: {conversation.conversation_id}</span>
            {userId && (
              <Link href={`/users/${userId}`} className="text-blue-600 hover:text-blue-500">
                View user
              </Link>
            )}
            {topic && <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-800">Topic: {topic}</span>}
            {costEstimate !== null && (
              <span className="text-xs text-gray-500">Estimated cost: ${costEstimate.toFixed(4)}</span>
            )}
          </div>
        </div>
        <ReloadButton onReload={() => refetch()} isLoading={isLoading} label="Reload conversation" />
      </div>

      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Created</dt>
          <dd className="text-sm text-gray-900">{formatDate(createdAt)}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Last updated</dt>
          <dd className="text-sm text-gray-900">{formatDate(updatedAt)}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Last message</dt>
          <dd className="text-sm text-gray-900">{formatDate(lastMessageAt)}</dd>
        </div>
      </dl>

      {conversation.proposed_brief && (
        <details className="rounded-md border border-gray-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-gray-700">
            Proposed brief
          </summary>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap text-xs text-gray-700">
            {formatJSON(conversation.proposed_brief)}
          </pre>
        </details>
      )}

      {conversation.accepted_brief && (
        <details className="rounded-md border border-gray-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-gray-700">
            Accepted brief
          </summary>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap text-xs text-gray-700">
            {formatJSON(conversation.accepted_brief)}
          </pre>
        </details>
      )}

      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Transcript</h3>
        <MessageTranscript messages={conversation.messages} />
      </div>
    </div>
  );
}
