/**
 * Lesson Details Component
 *
 * Shows detailed information about a specific lesson and its package.
 */

'use client';

import Link from 'next/link';
import { useLesson } from '../../queries';
import { useEffect, useState } from 'react';
import { AdminService } from '../../service';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { JSONViewer } from '../shared/JSONViewer';
import { LessonPackageViewer } from './LessonPackageViewer';
import { formatDate } from '@/lib/utils';

interface LessonDetailsProps {
  lessonId: string;
}

export function LessonDetails({ lessonId }: LessonDetailsProps) {
  const { data: lesson, isLoading, error, refetch } = useLesson(lessonId);
  const [unitRef, setUnitRef] = useState<{ unit_id: string; unit_title: string } | null>(null);

  useEffect(() => {
    const svc = new AdminService();
    svc
      .getLessonToUnitMap()
      .then((map) => setUnitRef(map[lessonId] ?? null))
      .catch(() => setUnitRef(null));
  }, [lessonId]);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading lesson details..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load lesson details. Please try again."
        onRetry={() => refetch()}
      />
    );
  }

  if (!lesson) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Lesson not found</h3>
        <p className="mt-2 text-gray-600">
          The requested lesson could not be found.
        </p>
        <Link
          href="/lessons"
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Back to lessons
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
              href="/lessons"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back to lessons
            </Link>
          </div>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">
            {lesson.title}
          </h1>
          <div className="mt-2 flex items-center space-x-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {lesson.learner_level}
            </span>
            {unitRef && (
              <Link
                href={`/units/${unitRef.unit_id}`}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 hover:bg-green-200"
              >
                Unit: {unitRef.unit_title}
              </Link>
            )}
            <span className="text-sm text-gray-500">
              Package v{lesson.package_version}
            </span>
          </div>
        </div>

        {/* Reload Button */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
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
            <span>{isLoading ? 'Reloading...' : 'Reload Lesson'}</span>
          </button>
        </div>
      </div>

      {/* Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Learner Level</h3>
            <p className="text-gray-900">{lesson.learner_level}</p>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Metadata</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Created:</span>
                <span className="text-gray-900">{formatDate(lesson.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Updated:</span>
                <span className="text-gray-900">{formatDate(lesson.updated_at)}</span>
              </div>
              {lesson.flow_run_id && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Created by Flow:</span>
                  <Link
                    href={`/flows/${lesson.flow_run_id}`}
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    View Flow Run
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Lesson Package */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Lesson Package</h2>
            <p className="text-sm text-gray-600 mt-1">
              Structured learning content including objectives, glossary, didactic materials, and assessments
            </p>
          </div>
          <button
            onClick={() => {
              const jsonWindow = window.open('', '_blank');
              if (jsonWindow) {
                jsonWindow.document.write(`
                  <html>
                    <head>
                      <title>Lesson Package JSON - ${lesson.title}</title>
                      <style>
                        body { font-family: monospace; margin: 20px; }
                        pre { white-space: pre-wrap; word-wrap: break-word; }
                      </style>
                    </head>
                    <body>
                      <h1>Lesson Package JSON</h1>
                      <h2>${lesson.title}</h2>
                      <pre>${JSON.stringify(lesson.package, null, 2)}</pre>
                    </body>
                  </html>
                `);
                jsonWindow.document.close();
              }
            }}
            className="inline-flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <span>View JSON</span>
          </button>
        </div>
        <div className="p-6">
          <LessonPackageViewer package={lesson.package} />
        </div>
      </div>

      {/* Source Material */}
      {lesson.source_material && (
        <div className="bg-white rounded-lg shadow p-6">
          <JSONViewer
            data={lesson.source_material}
            title="Source Material"
            maxHeight="max-h-64"
          />
        </div>
      )}

      {/* Mini lesson is displayed in package viewer */}
    </div>
  );
}
