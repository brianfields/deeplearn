/**
 * Message Transcript Component
 *
 * Renders the full transcript for a learning coach conversation.
 */

'use client';

import Link from 'next/link';
import type { ConversationMessage } from '../../models';
import { formatCost, formatDate, formatJSON, formatTokens } from '@/lib/utils';
import { ResizablePanel } from '../shared/ResizablePanel';

interface MessageTranscriptProps {
  messages: ConversationMessage[];
}

const ROLE_STYLES: Record<ConversationMessage['role'], string> = {
  user: 'bg-blue-100 text-blue-800 border-blue-200',
  assistant: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  system: 'bg-slate-100 text-slate-600 border-slate-200',
};

export function MessageTranscript({ messages }: MessageTranscriptProps) {
  if (!messages || messages.length === 0) {
    return <p className="text-sm text-gray-500">No messages recorded for this conversation.</p>;
  }

  return (
    <div className="space-y-4">
      {messages.map((message, index) => {
        const orderLabel = message.message_order ?? index + 1;
        const hasMetadata = Object.keys(message.metadata ?? {}).length > 0;

        return (
          <article
            key={message.id}
            className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
          >
            <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${ROLE_STYLES[message.role]}`}
                >
                  {message.role}
                </span>
                <span className="text-xs font-medium text-gray-500">Message {orderLabel}</span>
                {message.llm_request_id && (
                  <Link
                    href={`/llm-requests/${message.llm_request_id}`}
                    className="text-xs font-medium text-blue-600 hover:text-blue-500"
                  >
                    View LLM request
                  </Link>
                )}
              </div>
              <time className="text-xs text-gray-500">{formatDate(message.created_at)}</time>
            </header>

            <div className="mt-3 whitespace-pre-wrap text-sm text-gray-900">
              {message.content?.length ? message.content : <span className="italic text-gray-500">No content provided.</span>}
            </div>

            <footer className="mt-3 flex flex-wrap items-center gap-3 text-xs text-gray-500">
              <span>Tokens: {formatTokens(message.tokens_used)}</span>
              <span>Cost: {formatCost(message.cost_estimate)}</span>
            </footer>

            {hasMetadata && (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs font-medium text-gray-600">
                  Additional metadata
                </summary>
                <div className="mt-2 rounded border border-gray-200 bg-gray-50">
                  <ResizablePanel defaultHeight={256} minHeight={96} maxHeight={600}>
                    <pre className="p-3 text-xs text-gray-700">
                      {formatJSON(message.metadata)}
                    </pre>
                  </ResizablePanel>
                </div>
              </details>
            )}
          </article>
        );
      })}
    </div>
  );
}
