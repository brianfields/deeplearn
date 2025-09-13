/**
 * Flow Steps List Component
 *
 * Displays the steps within a flow run with expandable details.
 */

'use client';

import Link from 'next/link';
import { useState } from 'react';
import { StatusBadge } from '../shared/StatusBadge';
import { JSONViewer } from '../shared/JSONViewer';
import {
  formatDate,
  formatExecutionTime,
  formatCost,
  formatTokens
} from '@/lib/utils';
import { cn } from '@/lib/utils';
import type { FlowStepDetails } from '../../models';

interface FlowStepsListProps {
  steps: FlowStepDetails[];
  flowId: string;
}

export function FlowStepsList({ steps, flowId }: FlowStepsListProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  if (steps.length === 0) {
    return (
      <div className="px-6 py-8 text-center">
        <p className="text-gray-500">No steps found for this flow run</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {steps.map((step, index) => {
        const isExpanded = expandedSteps.has(step.id);

        return (
          <div key={step.id} className="px-6 py-4">
            {/* Step Header - Clickable */}
            <div
              className={cn(
                "flex items-center justify-between cursor-pointer rounded-lg p-3 transition-colors",
                "hover:bg-gray-50 border border-transparent hover:border-gray-200",
                isExpanded && "bg-blue-50 border-blue-200"
              )}
              onClick={() => toggleStep(step.id)}
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="flex-shrink-0">
                  <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
                    isExpanded
                      ? "bg-blue-600 text-white"
                      : "bg-blue-100 text-blue-600"
                  )}>
                    <span className="text-sm font-medium">
                      {step.step_order}
                    </span>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {step.step_name}
                    </h3>
                    <StatusBadge status={step.status} size="sm" />
                  </div>
                  <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <span>Duration: {formatExecutionTime(step.execution_time_ms)}</span>
                    <span>Tokens: {formatTokens(step.tokens_used)}</span>
                    <span>Cost: {formatCost(step.cost_estimate)}</span>
                    {step.llm_request_id && (
                      <span className="text-blue-600">Has LLM Request</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {/* Expand/Collapse Icon */}
                <div className="flex items-center space-x-2">
                  <svg
                    className={cn(
                      'w-5 h-5 text-gray-400 transition-transform',
                      isExpanded ? 'rotate-90' : 'rotate-0'
                    )}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  <span className="text-sm text-gray-500">
                    {isExpanded ? 'Collapse' : 'Expand'}
                  </span>
                </div>
              </div>
            </div>

            {/* LLM Request Link - Outside clickable area */}
            {step.llm_request_id && (
              <div className="mt-2 px-3">
                <Link
                  href={`/llm-requests/${step.llm_request_id}`}
                  className="inline-flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-500"
                  onClick={(e) => e.stopPropagation()}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  <span>View LLM Request Details</span>
                </Link>
              </div>
            )}

            {/* Error Message */}
            {step.error_message && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-700">{step.error_message}</p>
              </div>
            )}

            {/* Expanded Details */}
            {isExpanded && (
              <div className="mt-4 space-y-4 bg-gray-50 rounded-lg p-4">
                {/* Timeline */}
                <div className="bg-white rounded-md p-4 border">
                  <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                    <svg className="w-4 h-4 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Timeline
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-gray-600">Created:</span>
                      <span className="text-gray-900 font-medium">{formatDate(step.created_at)}</span>
                    </div>
                    {step.completed_at && (
                      <div className="flex items-center space-x-2 text-sm">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-gray-600">Completed:</span>
                        <span className="text-gray-900 font-medium">{formatDate(step.completed_at)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Input/Output Data */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <JSONViewer
                    data={step.inputs}
                    title="Input Data"
                    maxHeight="max-h-64"
                  />

                  {step.outputs && (
                    <JSONViewer
                      data={step.outputs}
                      title="Output Data"
                      maxHeight="max-h-64"
                    />
                  )}
                </div>

                {/* Metadata */}
                {step.step_metadata && (
                  <JSONViewer
                    data={step.step_metadata}
                    title="Step Metadata"
                    maxHeight="max-h-48"
                  />
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
