/**
 * Learning Session Detail Page
 *
 * Fetches and renders a single learning session with exercise answers.
 */

'use client';

import { useMemo } from 'react';
import { useLearningSession } from '@/modules/admin/queries';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';
import { LearningSessionDetails } from '@/modules/admin/components/learning-sessions/LearningSessionDetails';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { formatDate } from '@/lib/utils';

interface LearningSessionDetailPageProps {
  params: {
    sessionId: string;
  };
}

export default function LearningSessionDetailPage({ params }: LearningSessionDetailPageProps) {
  const sessionId = params.sessionId;
  const { data, isLoading, error, refetch } = useLearningSession(sessionId);

  const headerTitle = useMemo(() => {
    if (!data) {
      return `Session ${sessionId}`;
    }
    return `Session ${data.id}`;
  }, [data, sessionId]);

  if (isLoading && !data) {
    return <LoadingSpinner size="lg" text="Loading learning session..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load learning session. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  if (!data) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
        Learning session not found.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{headerTitle}</h1>
          <p className="mt-1 text-gray-600">
            Lesson {data.lesson_id} · Unit {data.unit_id ?? '—'}
          </p>
          <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-700">
            <span>Started: {data.started_at ? formatDate(data.started_at) : '—'}</span>
            <span>Completed: {data.completed_at ? formatDate(data.completed_at) : '—'}</span>
            <span>Progress: {data.progress_percentage.toFixed(1)}%</span>
            <span>User: {data.user_id ?? '—'}</span>
          </div>
        </div>
        <StatusBadge status={data.status} size="md" />
      </div>

      <LearningSessionDetails session={data} />
    </div>
  );
}
