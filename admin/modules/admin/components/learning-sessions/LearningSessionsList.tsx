/**
 * Learning Sessions List Component
 *
 * Displays a paginated table of learning sessions with expandable details.
 */

'use client';

import Link from 'next/link';
import { Fragment, useState } from 'react';
import { useLearningSessions } from '../../queries';
import { useAdminStore, useLearningSessionFilters } from '../../store';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { ReloadButton } from '../shared/ReloadButton';
import { StatusBadge } from '../shared/StatusBadge';
import { LearningSessionDetails } from './LearningSessionDetails';
import { formatDate } from '@/lib/utils';

export function LearningSessionsList() {
  const filters = useLearningSessionFilters();
  const { setLearningSessionFilters } = useAdminStore((state) => ({
    setLearningSessionFilters: state.setLearningSessionFilters,
  }));
  const { data, isLoading, error, refetch } = useLearningSessions(filters);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const sessions = data?.sessions ?? [];
  const totalCount = data?.total_count ?? 0;
  const currentPage = data?.page ?? filters.page ?? 1;
  const pageSize = data?.page_size ?? filters.page_size ?? 25;
  const hasNext = data?.has_next ?? false;
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(totalCount / pageSize)) : 1;

  const toggleExpanded = (sessionId: string) => {
    setExpandedRows((current) => {
      const next = new Set(current);
      if (next.has(sessionId)) {
        next.delete(sessionId);
      } else {
        next.add(sessionId);
      }
      return next;
    });
  };

  const handlePageChange = (page: number) => {
    if (page < 1) return;
    setLearningSessionFilters({ page });
  };

  const handlePageSizeChange = (size: number) => {
    setLearningSessionFilters({ page: 1, page_size: size });
  };

  if (isLoading && sessions.length === 0) {
    return <LoadingSpinner size="lg" text="Loading learning sessions..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load learning sessions. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-700">
          <span>
            Showing {sessions.length} of {totalCount} sessions
          </span>
          <ReloadButton onReload={() => refetch()} isLoading={isLoading} />
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-700">
          <label htmlFor="learning-session-page-size">Per page:</label>
          <select
            id="learning-session-page-size"
            value={pageSize}
            onChange={(event) => handlePageSizeChange(Number(event.target.value))}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {sessions.length === 0 ? (
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
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2h-3l-1-2h-6l-1 2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No learning sessions</h3>
            <p className="mt-1 text-sm text-gray-500">
              Learning sessions will appear here once learners begin working through lessons.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Lesson
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Completed
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sessions.map((session) => {
                  const isExpanded = expandedRows.has(session.id);
                  const startedAt = session.started_at ? formatDate(session.started_at) : '—';
                  const completedAt = session.completed_at ? formatDate(session.completed_at) : '—';
                  const progress = Number.isFinite(session.progress_percentage)
                    ? `${session.progress_percentage.toFixed(1)}%`
                    : '—';

                  return (
                    <Fragment key={session.id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <button
                              type="button"
                              onClick={() => toggleExpanded(session.id)}
                              className="rounded-full border border-gray-200 p-1 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
                              aria-label={isExpanded ? 'Collapse session details' : 'Expand session details'}
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
                              <div className="text-sm font-medium text-gray-900">Lesson {session.lesson_id}</div>
                              <div className="text-xs text-gray-500">Unit {session.unit_id ?? '—'}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {session.user_id ? (
                            <Link
                              href={`/users/${session.user_id}`}
                              className="text-blue-600 hover:text-blue-500"
                            >
                              {session.user_id}
                            </Link>
                          ) : (
                            <span className="text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={session.status} size="sm" />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{progress}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{startedAt}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{completedAt}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link
                            href={`/learning-sessions/${session.id}`}
                            className="text-blue-600 hover:text-blue-500"
                          >
                            View details
                          </Link>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="px-6 pb-6 pt-2">
                            <LearningSessionDetails session={session} />
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
          <div className="text-sm text-gray-500">Total: {totalCount} sessions</div>
        </div>
      )}
    </div>
  );
}
