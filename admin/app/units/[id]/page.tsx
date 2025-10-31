/**
 * Unit Details Page
 *
 * Shows unit metadata and ordered lessons.
 */

'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useUnit, useRetryUnit, useLesson } from '@/modules/admin/queries';
import {
  UnitPodcastList,
  derivePodcastPropsFromUnit,
} from '@/modules/admin/components/content/UnitPodcastList';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';
import { ReloadButton } from '@/modules/admin/components/shared/ReloadButton';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { ResourceList } from '@/modules/admin/components/resources/ResourceList';
import { formatDate } from '@/lib/utils';
import type { MCQExercise, ShortAnswerExercise } from '@/modules/admin/models';

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

function LessonExpandedDetails({ lessonId }: { lessonId: string }) {
  const { data: lesson, isLoading, error } = useLesson(lessonId);

  if (isLoading) {
    return (
      <div className="px-6 pb-4 pt-2 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center justify-center py-4">
          <LoadingSpinner size="sm" text="Loading lesson details..." />
        </div>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="px-6 pb-4 pt-2 bg-gray-50 border-t border-gray-100">
        <p className="text-sm text-red-600">Failed to load lesson details</p>
      </div>
    );
  }

  const mcqExercises = lesson.package.exercises.filter(
    (ex): ex is MCQExercise => ex.exercise_type === 'mcq'
  );

  const shortAnswerExercises = lesson.package.exercises.filter(
    (ex): ex is ShortAnswerExercise => ex.exercise_type === 'short_answer'
  );

  const allExercises = lesson.package.exercises;

  return (
    <div className="px-6 pb-4 pt-2 bg-gray-50 border-t border-gray-100 space-y-6 max-h-[70vh] overflow-y-auto">
      {/* Mini Lesson */}
      {lesson.package.mini_lesson && (
        <div>
          <h3 className="text-xs font-semibold text-gray-700 uppercase mb-1.5">Mini Lesson</h3>
          <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap bg-white rounded border border-gray-200 p-3 max-h-48 overflow-y-auto">
            {lesson.package.mini_lesson}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Learning Objectives */}
        {lesson.package.objectives && lesson.package.objectives.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-700 uppercase mb-1.5">
              Learning Objectives ({lesson.package.objectives.length})
            </h3>
            <ul className="space-y-2 text-xs">
              {lesson.package.objectives.map((obj) => (
                <li key={obj.id} className="text-gray-700">
                  <p className="font-semibold text-gray-800">
                    {obj.title || obj.text || obj.description || obj.id}
                  </p>
                  {(obj.description || obj.text) && (
                    <p className="mt-0.5 text-gray-600">
                      {obj.description || obj.text}
                    </p>
                  )}
                  {obj.bloom_level && (
                    <p className="mt-0.5 text-gray-400 uppercase tracking-wide">
                      Bloom level: {obj.bloom_level}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Key Concepts from Glossary */}
        {lesson.package.glossary && Object.keys(lesson.package.glossary).length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-700 uppercase mb-1.5">
              Key Concepts ({Object.values(lesson.package.glossary).flat().length})
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {Object.values(lesson.package.glossary)
                .flat()
                .map((term) => (
                  <span
                    key={term.id}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                    title={term.definition}
                  >
                    {term.term}
                  </span>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* All Exercises - Unified Section */}
      {allExercises.length > 0 && (
        <div>
          <div className="mb-3">
            <h3 className="text-xs font-semibold text-gray-700 uppercase mb-2">
              Exercises ({allExercises.length} total)
            </h3>
            <div className="text-xs text-gray-500 mb-3">
              {mcqExercises.length > 0 && <span className="mr-4">• {mcqExercises.length} MCQ</span>}
              {shortAnswerExercises.length > 0 && <span>• {shortAnswerExercises.length} Short Answer</span>}
            </div>
          </div>

          <div className="space-y-4">
            {/* MCQ Exercises */}
            {mcqExercises.length > 0 && (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide border-b border-gray-300 pb-2">
                  Multiple Choice Questions
                </div>
                {mcqExercises.map((exercise, idx) => (
                  <div key={exercise.id} className="bg-white rounded border border-gray-200 p-4 hover:shadow-sm transition-shadow">
                    <div className="font-semibold text-gray-900 mb-2">
                      MCQ {idx + 1}. {exercise.stem}
                    </div>
                    <ul className="space-y-1.5 ml-3 mb-3">
                      {exercise.options.map((opt) => (
                        <li
                          key={opt.id}
                          className={`text-sm ${
                            opt.label === exercise.answer_key.label
                              ? 'text-green-700 font-semibold bg-green-50 -ml-3 px-3 py-1 rounded'
                              : 'text-gray-600'
                          }`}
                        >
                          <span className="font-medium">{opt.label}.</span> {opt.text}
                        </li>
                      ))}
                    </ul>
                    {exercise.answer_key.rationale_right && (
                      <div className="text-xs bg-green-50 border border-green-200 rounded p-2 text-green-700">
                        <span className="font-semibold">Explanation: </span>
                        {exercise.answer_key.rationale_right}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Short Answer Exercises */}
            {shortAnswerExercises.length > 0 && (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide border-b border-gray-300 pb-2">
                  Short Answer Exercises
                </div>
                {shortAnswerExercises.map((exercise, idx) => (
                  <div key={exercise.id} className="bg-white rounded border border-blue-200 p-4 hover:shadow-sm transition-shadow">
                    <div className="mb-3">
                      <div className="font-semibold text-gray-900 mb-1">
                        Short Answer {idx + 1}. {exercise.stem}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                      {/* Canonical Answer */}
                      <div className="bg-blue-50 rounded p-3 border border-blue-100">
                        <p className="text-xs font-semibold uppercase text-blue-700 mb-1">Canonical Answer</p>
                        <p className="text-sm text-gray-900 font-medium">{exercise.canonical_answer || '—'}</p>
                      </div>

                      {/* Acceptable Answers */}
                      <div className="bg-blue-50 rounded p-3 border border-blue-100">
                        <p className="text-xs font-semibold uppercase text-blue-700 mb-1">
                          Acceptable Answers ({exercise.acceptable_answers.length})
                        </p>
                        {exercise.acceptable_answers.length > 0 ? (
                          <ul className="text-sm text-gray-900 space-y-0.5">
                            {exercise.acceptable_answers.map((answer, aIdx) => (
                              <li key={aIdx} className="flex items-start">
                                <span className="mr-2">•</span>
                                <span>{answer}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-gray-500 italic">None specified</p>
                        )}
                      </div>
                    </div>

                    {/* Common Wrong Answers & Misconceptions */}
                    {exercise.wrong_answers.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold uppercase text-gray-600 mb-2">Common Misconceptions</p>
                        <div className="space-y-2">
                          {exercise.wrong_answers.map((wrongAnswer, wIdx) => (
                            <div key={`${exercise.id}-wrong-${wIdx}`} className="bg-amber-50 border border-amber-200 rounded p-2.5">
                              <p className="text-sm font-medium text-gray-900 mb-1">
                                Wrong: <span className="text-amber-700">{wrongAnswer.answer || '—'}</span>
                              </p>
                              <p className="text-xs text-gray-700 mb-1">
                                <span className="font-semibold">Why: </span>
                                {wrongAnswer.explanation || '—'}
                              </p>
                              {wrongAnswer.misconception_ids && wrongAnswer.misconception_ids.length > 0 && (
                                <p className="text-xs text-gray-500">
                                  <span className="font-semibold">Misconceptions: </span>
                                  {wrongAnswer.misconception_ids.join(', ')}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Correct Answer Feedback */}
                    {exercise.explanation_correct && (
                      <div className="bg-green-50 border border-green-200 rounded p-3">
                        <p className="text-xs font-semibold uppercase text-green-700 mb-1">Correct Answer Feedback</p>
                        <p className="text-sm text-gray-900 whitespace-pre-wrap">{exercise.explanation_correct}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Flow Run / LLM Request Link */}
      {lesson.flow_run_id && (
        <div className="pt-3 border-t border-gray-200">
          <Link
            href={`/flows/${lesson.flow_run_id}`}
            className="inline-flex items-center text-xs font-medium text-blue-600 hover:text-blue-800"
          >
            View Flow Run & LLM Requests →
          </Link>
        </div>
      )}
    </div>
  );
}

export default function UnitDetailsPage({ params }: UnitDetailsPageProps) {
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

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Unit Artwork</h2>
          <p className="text-sm text-gray-600">AI-generated hero image and prompt</p>
        </div>
        <div className="px-6 py-6 grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-slate-900 text-white min-h-[220px] flex items-center justify-center">
            {unit.art_image_url ? (
              <img
                src={unit.art_image_url}
                alt={`${unit.title} artwork`}
                className="w-full h-full object-cover"
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

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Source Resources</h2>
          <p className="text-sm text-gray-500">
            Learner-provided resources and any generated supplemental material used to build this
            unit.
          </p>
        </div>
        <ResourceList
          resources={resourceSummaries}
          emptyMessage="No source resources attached to this unit yet."
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

      {/* Unit-level Learning Objectives & Source Material */}
      {(unit.learning_objectives || unit.source_material) && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Unit Overview</h2>
            <p className="text-sm text-gray-600">Learning objectives and source material</p>
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
            {unit.source_material && (
              <div className="md:col-span-1">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Source Material</h3>
                <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm text-gray-700 whitespace-pre-wrap max-h-72 overflow-auto">
                  {unit.source_material}
                </div>
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
