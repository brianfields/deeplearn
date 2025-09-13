/**
 * LLM Request Details Component
 *
 * Shows detailed information about a specific LLM request.
 */

'use client';

import Link from 'next/link';
import { useLLMRequest } from '../../queries';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { StatusBadge } from '../shared/StatusBadge';
import { JSONViewer } from '../shared/JSONViewer';
import { CodeBlock } from '../shared/CodeBlock';
import {
  formatDate,
  formatExecutionTime,
  formatCost,
  formatTokens
} from '@/lib/utils';

interface LLMRequestDetailsProps {
  requestId: string;
}

export function LLMRequestDetails({ requestId }: LLMRequestDetailsProps) {
  const { data: request, isLoading, error, refetch } = useLLMRequest(requestId);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading LLM request details..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load LLM request details. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  if (!request) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Request not found</h3>
        <p className="mt-2 text-gray-600">
          The requested LLM request could not be found.
        </p>
        <Link
          href="/llm-requests"
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Back to requests
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Link
              href="/llm-requests"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back to requests
            </Link>
          </div>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">
            LLM Request Details
          </h1>
          <div className="mt-2 flex items-center space-x-4">
            <StatusBadge status={request.status} />
            <span className="text-sm text-gray-500">
              {request.provider} / {request.model}
            </span>
            <span className="text-sm text-gray-500">
              {request.api_variant}
            </span>
            {request.cached && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Cached
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Duration</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatExecutionTime(request.execution_time_ms)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Tokens</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatTokens(request.tokens_used)}
              </p>
              {request.input_tokens && request.output_tokens && (
                <p className="text-xs text-gray-500">
                  {formatTokens(request.input_tokens)} in / {formatTokens(request.output_tokens)} out
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Cost</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCost(request.cost_estimate)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-gray-100 rounded-md flex items-center justify-center">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Retry Attempt</p>
              <p className="text-lg font-semibold text-gray-900">
                {request.retry_attempt}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Request Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Temperature</dt>
            <dd className="mt-1 text-sm text-gray-900">{request.temperature}</dd>
          </div>
          {request.max_output_tokens && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Max Output Tokens</dt>
              <dd className="mt-1 text-sm text-gray-900">{request.max_output_tokens}</dd>
            </div>
          )}
          {request.provider_response_id && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Provider Response ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono text-xs">
                {request.provider_response_id}
              </dd>
            </div>
          )}
          {request.system_fingerprint && (
            <div>
              <dt className="text-sm font-medium text-gray-500">System Fingerprint</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono text-xs">
                {request.system_fingerprint}
              </dd>
            </div>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Timeline</h2>
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Created:</span>
            <span className="text-sm font-medium text-gray-900">
              {formatDate(request.created_at)}
            </span>
          </div>
          {request.response_created_at && (
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Response received:</span>
              <span className="text-sm font-medium text-gray-900">
                {formatDate(request.response_created_at)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {request.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-red-800">Error</h3>
          <p className="mt-1 text-sm text-red-700">{request.error_message}</p>
          {request.error_type && (
            <p className="mt-1 text-xs text-red-600">Type: {request.error_type}</p>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Conversation</h2>
        <div className="space-y-4">
          {request.messages.map((message, index) => (
            <div key={index}>
              <CodeBlock
                content={message.content}
                title={`${message.role.charAt(0).toUpperCase() + message.role.slice(1)} Message`}
                maxHeight="max-h-64"
                className={
                  message.role === 'user'
                    ? 'border-l-4 border-blue-400'
                    : message.role === 'assistant'
                    ? 'border-l-4 border-green-400'
                    : 'border-l-4 border-gray-400'
                }
              />
            </div>
          ))}
        </div>
      </div>

      {/* Response Content */}
      {request.response_content && (
        <div className="bg-white rounded-lg shadow p-6">
          <CodeBlock
            content={request.response_content}
            title="Response Content"
            maxHeight="max-h-96"
          />
        </div>
      )}

      {/* Raw Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {request.request_payload && (
          <div className="bg-white rounded-lg shadow p-6">
            <JSONViewer
              data={request.request_payload}
              title="Request Payload"
              maxHeight="max-h-96"
            />
          </div>
        )}

        {request.response_raw && (
          <div className="bg-white rounded-lg shadow p-6">
            <JSONViewer
              data={request.response_raw}
              title="Raw Response"
              maxHeight="max-h-96"
            />
          </div>
        )}
      </div>

      {/* Additional Parameters */}
      {request.additional_params && (
        <div className="bg-white rounded-lg shadow p-6">
          <JSONViewer
            data={request.additional_params}
            title="Additional Parameters"
            maxHeight="max-h-64"
          />
        </div>
      )}
    </div>
  );
}
