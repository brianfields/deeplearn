/**
 * Lessons List Component
 *
 * Displays paginated list of lessons with search and filtering.
 */

'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useLessons } from '../../queries';
import { useLessonFilters, useAdminStore } from '../../store';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { formatDate } from '@/lib/utils';

export function LessonsList() {
  const filters = useLessonFilters();
  const { setLessonFilters } = useAdminStore();

  const { data, isLoading, error, refetch } = useLessons(filters);

  const handlePageChange = (newPage: number) => {
    setLessonFilters({ page: newPage });
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setLessonFilters({ page: 1, page_size: newPageSize });
  };

  const handleSearchChange = (search: string) => {
    setLessonFilters({ page: 1, search: search || undefined });
  };

  const handleLevelFilter = (user_level: string) => {
    setLessonFilters({ page: 1, user_level: user_level || undefined });
  };

  const handleDomainFilter = (domain: string) => {
    setLessonFilters({ page: 1, domain: domain || undefined });
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading lessons..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load lessons. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  const lessons = data?.lessons || [];
  const totalCount = data?.total_count || 0;
  const currentPage = data?.page || 1;
  const pageSize = data?.page_size || 10;
  const hasNext = data?.has_next || false;
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              id="search"
              type="text"
              placeholder="Search lessons..."
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="level" className="block text-sm font-medium text-gray-700 mb-2">
              User Level
            </label>
            <select
              id="level"
              value={filters.user_level || ''}
              onChange={(e) => handleLevelFilter(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">All Levels</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div>
            <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-2">
              Domain
            </label>
            <select
              id="domain"
              value={filters.domain || ''}
              onChange={(e) => handleDomainFilter(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">All Domains</option>
              <option value="mathematics">Mathematics</option>
              <option value="science">Science</option>
              <option value="history">History</option>
              <option value="literature">Literature</option>
              <option value="programming">Programming</option>
            </select>
          </div>
        </div>
      </div>

      {/* Header with pagination info and reload */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-gray-700">
            Showing {lessons.length} of {totalCount} lessons
          </p>
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="inline-flex items-center space-x-1 px-3 py-1 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>{isLoading ? 'Reloading...' : 'Reload'}</span>
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <label htmlFor="pageSize" className="text-sm text-gray-700">
            Per page:
          </label>
          <select
            id="pageSize"
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* Lessons grid */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {lessons.length === 0 ? (
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
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No lessons found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {filters.search || filters.user_level || filters.domain
                ? 'Try adjusting your filters to see more results.'
                : 'No lessons have been created yet.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
            {lessons.map((lesson) => (
              <div key={lesson.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <Link
                      href={`/lessons/${lesson.id}`}
                      className="text-lg font-medium text-blue-600 hover:text-blue-500 line-clamp-2"
                    >
                      {lesson.title}
                    </Link>
                    <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                      {lesson.core_concept}
                    </p>
                    <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {lesson.user_level}
                      </span>
                      {lesson.source_domain && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {lesson.source_domain}
                        </span>
                      )}
                      <span className="text-xs text-gray-400">
                        v{lesson.package_version}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-400">
                      Created: {formatDate(lesson.created_at)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!hasNext}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="text-sm text-gray-500">
            Total: {totalCount} lessons
          </div>
        </div>
      )}
    </div>
  );
}
