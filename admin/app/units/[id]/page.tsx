/**
 * Unit Details Page
 *
 * Shows unit metadata and ordered lessons.
 */

'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import { useUnit, useRetryUnit, useLesson } from '@/modules/admin/queries';
import {
  UnitPodcastList,
  derivePodcastPropsFromUnit,
} from '@/modules/admin/components/content/UnitPodcastList';
import { ConceptGlossaryView } from '@/modules/admin/components/content/ConceptGlossaryView';
import { ExerciseBankView } from '@/modules/admin/components/content/ExerciseBankView';
import { QuizStructureView } from '@/modules/admin/components/content/QuizStructureView';
import { QuizMetadataView } from '@/modules/admin/components/content/QuizMetadataView';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';
import { ReloadButton } from '@/modules/admin/components/shared/ReloadButton';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { ResourceList } from '@/modules/admin/components/resources/ResourceList';
import { formatDate } from '@/lib/utils';

interface UnitDetailsPageProps {
  params: { id: string };
}

function computeInitials(title: string): string {
  return (
    title
      ?.trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 3)
      .map(word => word[0]?.toUpperCase() ?? '')
      .join('') || 'U'
  );
}

function LessonExpandedDetails({ lessonId export default function UnitDetailsPage({ params }: UnitDetailsPageProps) {
  const { data: unit, isLoading, error, refetch } = useUnit(params.id);
  const retryUnit = useRetryUnit();
  const [expandedLessonId, setExpandedLessonId] = useState<string | null>(null);

  if (isLoading) return <LoadingSpinner size="lg" text="Loading unit..." />;
  if (error) return <ErrorMessage message="Failed to load unit." onRetry={() => refetch()} />;
  if (!unit)
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Unit not found</h3>
        <Link href="/units" className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          Back to units
        </Link>
      </div>
    );

  const isRetrying = retryUnit.isPending;
  const podcastProps = derivePodcastPropsFromUnit(unit);
  const resourceSummaries = unit.resources ?? [];

  const handleRetry = () => {
    if (retryUnit.isPending) {
      return;
    }
    retryUnit.mutate(unit.id, {
      onSuccess: () => {
        void refetch();
      },
    });
  };

  const toggleLesson = (lessonId: string) => {
    setExpandedLessonId(expandedLessonId === lessonId ? null : lessonId);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/units" className="text-sm text-gray-500 hover:text-gray-700">← Back to units</Link>
          <div className="mt-2 flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{unit.title}</h1>
            {unit.status && <StatusBadge status={unit.status} size="sm" />}
          </div>
          <div className="mt-2 flex items-center flex-wrap gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">{unit.learner_level}</span>
            <span className="text-sm text-gray-500">{unit.lessons.length} lessons</span>
            {typeof unit.target_lesson_count === 'number' && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">Target: {unit.target_lesson_count} lessons</span>
            )}
            <span
              data-testid={`flow-type-${unit.id}`}
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${unit.flow_type === 'fast' ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-800'}`}
              title={`Flow: ${unit.flow_type}`}
            >
              {unit.flow_type === 'fast' ? 'Fast flow' : 'Standard flow'}
            </span>
            {unit.generated_from_topic && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">Topic-generated</span>
            )}
          </div>
          {unit.description && <p className="mt-3 text-gray-700 max-w-3xl">{unit.description}</p>}
        </div>
        <ReloadButton
          onReload={() => {
            void refetch();
          }}
          isLoading={isLoading || isRetrying}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase text-gray-500">Status</p>
          <div className="mt-2 flex items-center gap-2 text-sm text-gray-700">
            <StatusBadge status={unit.status ?? 'unknown'} size="sm" />
            <span>{unit.status ?? 'unknown'}</span>
          </div>
          <p className="mt-2 text-xs text-gray-500">Last updated {formatDate(unit.updated_at)}</p>
          {unit.status === 'failed' && (
            <button
              type="button"
              onClick={handleRetry}
              disabled={isRetrying}
              className="mt-3 inline-flex items-center rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRetrying ? 'Retrying…' : 'Retry unit'}
            </button>
          )}
          {unit.arq_task_id && (
            <div className="mt-3">
              <Link
                href={`/tasks?taskId=${unit.arq_task_id}`}
                className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100"
              >
                View Creation Task →
              </Link>
            </div>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase text-gray-500">Creation progress</p>
          {unit.creation_progress ? (
            <div className="mt-2 text-sm text-gray-700">
              <p className="font-medium">Stage: {unit.creation_progress.stage ?? '—'}</p>
              {unit.creation_progress.message && (
                <p className="mt-1 text-xs text-gray-500">{unit.creation_progress.message}</p>
              )}
            </div>
          ) : (
            <p className="mt-2 text-sm text-gray-500">No progress metadata recorded.</p>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase text-gray-500">Content Summary</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm text-gray-700">{unit.lessons.length} lessons</p>
            <p className="text-xs text-gray-500">
              {unit.lessons.reduce((sum, l) => sum + l.exercise_count, 0)} total exercises
            </p>
            {podcastProps.introPodcast && (
              <p className="text-xs text-green-600 font-medium">✓ Intro podcast available</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Unit Artwork</h2>
          <p className="text-sm text-gray-600">AI-generated hero image and prompt</p>
        </div>
        <div className="px-6 py-6 grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-slate-900 text-white min-h-[220px] flex items-center justify-center">
            {unit.art_image_url ? (
              <Image
                src={unit.art_image_url}
                alt={`${unit.title} artwork`}
                layout="fill"
                objectFit="cover"
              />
            ) : (
              <div className="text-center space-y-2">
                <div className="text-4xl font-semibold tracking-[0.4em]">
                  {computeInitials(unit.title)}
                </div>
                <p className="text-sm text-slate-300">Artwork not available</p>
              </div>
            )}
          </div>
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-700">Generation Prompt</h3>
            {unit.art_image_description ? (
              <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-line">
                {unit.art_image_description}
              </p>
            ) : (
              <p className="text-sm text-gray-500">No generation prompt provided.</p>
            )}
          </div>
        </div>
      </div>

      <UnitPodcastList {...podcastProps} />

      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Source Resources</h2>
          <p className="text-sm text-gray-500">
            Learner-provided resources and any generated supplemental material used to build this
            unit.
          </p>
        </div>

        {/* Resource List */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Resources</h3>
          <ResourceList
            resources={resourceSummaries}
            emptyMessage="No source resources attached to this unit yet."
          />
        </div>

        {/* Source Material Preview */}
        {unit.source_material && (
          <div className="border-t border-gray-200 pt-6">
            <div className="flex items-center justify-between mb-3 gap-4">
              <h3 className="text-sm font-semibold text-gray-700">Consolidated Source Material</h3>
              <a
                href={`data:text/plain;charset=utf-8,${encodeURIComponent(unit.source_material)}`}
                download={`${unit.title || 'source-material'}.txt`}
                className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded border border-blue-200"
              >
                <span>↓</span>
                Download
              </a>
            </div>
            <div className="bg-gray-50 rounded border border-gray-200 p-4 text-xs text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
              {unit.source_material}
            </div>
          </div>
        )}
      </div>


      {/* Unit-level Learning Objectives & Source Material */}
      {(unit.learning_objectives) && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Learning Objectives</h2>
            <p className="text-sm text-gray-600">Unit-level learning objectives</p>
          </div>
          <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-6">
            {unit.learning_objectives && unit.learning_objectives.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Learning Objectives</h3>
                <ul className="space-y-3">
                  {unit.learning_objectives.map((lo) => (
                    <li key={lo.id} className="rounded-md border border-gray-200 p-3">
                      <p className="text-sm font-semibold text-gray-900">
                        {lo.title || lo.description || lo.id}
                      </p>
                      {lo.description && (
                        <p className="mt-0.5 text-sm text-gray-600">{lo.description}</p>
                      )}
                      {(lo.bloom_level || lo.evidence_of_mastery) && (
                        <div className="mt-1 space-y-0.5 text-xs text-gray-500">
                          {lo.bloom_level && <p>Bloom level: {lo.bloom_level}</p>}
                          {lo.evidence_of_mastery && <p>Evidence: {lo.evidence_of_mastery}</p>}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

          </div>
        </div>
      )}

      {unit.learning_objective_progress && unit.learning_objective_progress.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Learning Objective Progress</h2>
            <p className="text-sm text-gray-600">Based on recorded exercise attempts across this unit.</p>
          </div>
          <div className="px-6 py-4 space-y-4">
            {unit.learning_objective_progress.map((lo, idx) => {
              const percent = Math.min(Math.max(lo.progress_percentage ?? 0, 0), 100);
              return (
                <div key={`${lo.objective}-${idx}`} className="space-y-2">
                  <div className="flex items-center justify-between text-sm font-medium text-gray-700">
                    <span>{lo.objective}</span>
                    <span>
                      {lo.exercises_correct}/{lo.exercises_total} correct
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-green-500"
                      style={{ width: `${percent}%` }}
                      aria-hidden="true"
                    />
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round(percent)}% complete
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {unit.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {unit.error_message}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Lessons</h2>
          <p className="text-sm text-gray-600">Ordered lessons in this unit (click to expand details)</p>
        </div>
        <ul className="divide-y divide-gray-200">
          {unit.lessons.map((l, idx) => {
            const isExpanded = expandedLessonId === l.id;
            return (
              <li key={l.id} className="transition-colors hover:bg-gray-50">
                <button
                  onClick={() => toggleLesson(l.id)}
                  className="w-full px-6 py-3 flex items-center justify-between text-left focus:outline-none focus:bg-gray-50"
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <span className="w-7 h-7 inline-flex items-center justify-center rounded-full bg-gray-100 text-gray-700 text-xs font-medium flex-shrink-0">{idx + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-gray-900 font-medium text-sm">{l.title}</div>
                      <div className="mt-0.5 text-xs text-gray-500">
                        {l.learner_level ?? 'beginner'} • {l.exercise_count} exercises • {l.learning_objectives.length} objectives
                      </div>
                    </div>
                  </div>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ml-3 ${isExpanded ? 'transform rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {isExpanded && <LessonExpandedDetails lessonId={l.id} />}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
