/**
 * Learning Sessions List Component
 *
 * Displays a paginated table of learning sessions with links to detail pages.
 */

'use client';

import Link from 'next/link';
import { useLearningSessions } from '../../queries';
import { useAdminStore, useLearningSessionFilters } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { DetailViewTable, type DetailViewTableColumn } from '../shared/DetailViewTable';
import { formatDate } from '@/lib/utils';
import type { LearningSessionSummary } from '../../models';

export function LearningSessionsList(): JSX.Element {
  const filters = useLearningSessionFilters();
  const { setLearningSessionFilters } = useAdminStore((state) => ({
    setLearningSessionFilters: state.setLearningSessionFilters,
  }));
  const { data, isLoading, error, refetch } = useLearningSessions(filters);

  const sessions = data?.sessions ?? [];
  const totalCount = data?.total_count ?? 0;
  const currentPage = data?.page ?? filters.page ?? 1;
  const pageSize = data?.page_size ?? filters.page_size ?? 10;
  const hasNext = data?.has_next ?? false;
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(totalCount / pageSize)) : 1;

  const handlePageChange = (page: number) => {
    if (page < 1) return;
    setLearningSessionFilters({ page });
  };

  const handlePageSizeChange = (size: number) => {
    setLearningSessionFilters({ page: 1, page_size: size });
  };

  const PAGE_SIZE_OPTIONS = [10, 25, 50];

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
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2h-3l-1-2h-6l-1 2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
  );

  const columns: DetailViewTableColumn<LearningSessionSummary>[] = [
    {
      key: 'lesson',
      label: 'Lesson',
      render: (session) => (
        <div>
          <div className="text-sm font-medium text-gray-900">Lesson {session.lesson_id}</div>
          <div className="text-xs text-gray-500">Unit {session.unit_id ?? '—'}</div>
        </div>
      ),
    },
    {
      key: 'user_id',
      label: 'User',
      render: (session) =>
        session.user_id ? (
          <Link
            href={`/users/${session.user_id}`}
            className="text-blue-600 hover:text-blue-500"
            onClick={(e) => e.stopPropagation()}
          >
            {session.user_id}
          </Link>
        ) : (
          <span className="text-gray-500">—</span>
        ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (session) => <StatusBadge status={session.status} size="sm" />,
    },
    {
      key: 'progress',
      label: 'Progress',
      render: (session) => {
        const progress = Number.isFinite(session.progress_percentage)
          ? `${session.progress_percentage.toFixed(1)}%`
          : '—';
        return progress;
      },
    },
    {
      key: 'started_at',
      label: 'Started',
      render: (session) => (session.started_at ? formatDate(session.started_at) : '—'),
    },
    {
      key: 'completed_at',
      label: 'Completed',
      render: (session) => (session.completed_at ? formatDate(session.completed_at) : '—'),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-700">
          <span>
            Showing {sessions.length} of {totalCount} sessions
          </span>
        </div>
      </div>

      <DetailViewTable
        data={sessions}
        columns={columns}
        getRowId={(session) => session.id}
        getDetailHref={(session) => `/learning-sessions/${session.id}`}
        isLoading={isLoading && sessions.length === 0}
        error={error}
        emptyMessage="Learning sessions will appear here once learners begin working through lessons."
        emptyIcon={emptyIcon}
        onRetry={() => refetch()}
        pagination={{
          currentPage,
          totalPages,
          totalCount,
          pageSize,
          hasNext,
        }}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        pageOptions={PAGE_SIZE_OPTIONS}
      />
    </div>
  );
}
