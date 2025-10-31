/**
 * Learning Session Details Component
 *
 * Displays per-exercise answers for a learning session when expanded in the table.
 */

'use client';

import { useMemo } from 'react';

import type {
  LearningSessionSummary,
  LessonExercise,
  ShortAnswerExercise,
} from '@/modules/admin/models';
import { useLesson } from '@/modules/admin/queries';
import { formatDate } from '@/lib/utils';

interface LearningSessionDetailsProps {
  session: LearningSessionSummary;
}

export function LearningSessionDetails({ session }: LearningSessionDetailsProps) {
  const exerciseAnswers = (session.session_data?.exercise_answers ?? {}) as Record<string, any>;
  const exerciseIds = Object.keys(exerciseAnswers);
  const { data: lessonDetail, isLoading: isLessonLoading } = useLesson(session.lesson_id);

  const exerciseMetadata = useMemo(() => {
    const map = new Map<string, LessonExercise>();
    const exercises = lessonDetail?.package?.exercises ?? [];
    for (const exercise of exercises) {
      if (exercise?.id) {
        map.set(exercise.id, exercise);
      }
    }
    return map;
  }, [lessonDetail?.package?.exercises]);

  const renderExerciseMetadata = (exerciseId: string) => {
    if (isLessonLoading) {
      return (
        <div className="rounded-md border border-dashed border-gray-300 bg-gray-50 p-3 text-xs text-gray-500">
          Loading exercise metadata…
        </div>
      );
    }

    const metadata = exerciseMetadata.get(exerciseId);
    if (!metadata) {
      return (
        <div className="rounded-md border border-dashed border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">
          Lesson content for this exercise is unavailable.
        </div>
      );
    }

    const misconceptionSummary = metadata.misconceptions_used?.length
      ? metadata.misconceptions_used.join(', ')
      : 'None';

    const badges = [
      metadata.lo_id ? `LO: ${metadata.lo_id}` : null,
      metadata.cognitive_level ? `Cognitive: ${metadata.cognitive_level}` : null,
      metadata.estimated_difficulty ? `Difficulty: ${metadata.estimated_difficulty}` : null,
      `Misconceptions: ${misconceptionSummary}`,
    ].filter(Boolean) as string[];

    const renderShortAnswerDetails = (exercise: ShortAnswerExercise) => {
      return (
        <div className="space-y-3">
          <div>
            <p className="text-xs font-semibold uppercase text-gray-500">Prompt</p>
            <p className="whitespace-pre-wrap text-sm text-gray-900">{exercise.stem}</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase text-gray-500">Canonical Answer</p>
              <p className="text-sm text-gray-900">{exercise.canonical_answer || '—'}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-gray-500">Acceptable Answers</p>
              {exercise.acceptable_answers.length > 0 ? (
                <ul className="list-inside list-disc text-sm text-gray-900">
                  {exercise.acceptable_answers.map((answer) => (
                    <li key={answer}>{answer}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-900">None</p>
              )}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-gray-500">Common Misconceptions</p>
            {exercise.wrong_answers.length > 0 ? (
              <ul className="space-y-2">
                {exercise.wrong_answers.map((wrongAnswer) => (
                  <li key={`${wrongAnswer.answer}-${wrongAnswer.explanation}`} className="rounded-md bg-gray-50 p-2">
                    <p className="text-sm font-medium text-gray-900">Answer: {wrongAnswer.answer || '—'}</p>
                    <p className="text-xs text-gray-600">Explanation: {wrongAnswer.explanation || '—'}</p>
                    {wrongAnswer.misconception_ids.length > 0 && (
                      <p className="text-xs text-gray-500">
                        Misconception IDs: {wrongAnswer.misconception_ids.join(', ')}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-900">None listed</p>
            )}
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-gray-500">Correct Answer Feedback</p>
            <p className="whitespace-pre-wrap text-sm text-gray-900">
              {exercise.explanation_correct || '—'}
            </p>
          </div>
        </div>
      );
    };

    return (
      <div className="space-y-3">
        {badges.length > 0 && (
          <div className="flex flex-wrap gap-2 text-xs text-gray-600">
            {badges.map((badge) => (
              <span key={badge} className="rounded-full bg-gray-100 px-2 py-1">
                {badge}
              </span>
            ))}
          </div>
        )}
        {metadata.exercise_type === 'short_answer'
          ? renderShortAnswerDetails(metadata as ShortAnswerExercise)
          : (
              <div>
                <p className="text-xs font-semibold uppercase text-gray-500">Prompt</p>
                <p className="whitespace-pre-wrap text-sm text-gray-900">
                  {'stem' in metadata && typeof metadata.stem === 'string' ? metadata.stem : '—'}
                </p>
              </div>
            )}
      </div>
    );
  };

  if (exerciseIds.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">
        No exercise answers were recorded for this session.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {exerciseIds.map((exerciseId) => {
        const answer = exerciseAnswers[exerciseId] ?? {};
        const attemptHistory: Array<Record<string, any>> = Array.isArray(answer.attempt_history)
          ? answer.attempt_history
          : [];
        const lastSubmittedAt = attemptHistory.at(-1)?.submitted_at ?? answer.completed_at ?? null;

        return (
          <div key={exerciseId} className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-gray-900">Exercise {exerciseId}</h4>
                  <p className="text-xs text-gray-500">Type: {answer.exercise_type ?? 'unknown'}</p>
                </div>
                <div className="flex flex-wrap gap-3 text-xs text-gray-600">
                  <span>Attempts: {answer.attempts ?? attemptHistory.length ?? 0}</span>
                  <span>Correct: {answer.has_been_answered_correctly ? 'Yes' : 'No'}</span>
                  <span>
                    Time Spent: {typeof answer.time_spent_seconds === 'number' ? `${answer.time_spent_seconds}s` : '—'}
                  </span>
                  <span>
                    Last Submitted:{' '}
                    {lastSubmittedAt ? formatDate(lastSubmittedAt) : '—'}
                  </span>
                </div>
              </div>
            </div>

            <div className="px-4 py-4">
              <div className="mb-4">
                {renderExerciseMetadata(exerciseId)}
              </div>
              <div className="overflow-hidden rounded-md border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Attempt
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Submitted At
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Correct
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Time Spent (s)
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Answer
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 bg-white">
                    {attemptHistory.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-3 text-center text-sm text-gray-500">
                          No attempts recorded
                        </td>
                      </tr>
                    ) : (
                      attemptHistory.map((attempt, index) => {
                        const submittedAt = attempt.submitted_at ?? null;
                        const answerContent = attempt.user_answer;
                        const serializedAnswer =
                          typeof answerContent === 'string'
                            ? answerContent
                            : answerContent
                              ? JSON.stringify(answerContent, null, 2)
                              : '—';

                        return (
                          <tr key={`${exerciseId}-attempt-${index}`} className="hover:bg-gray-50">
                            <td className="px-4 py-2 text-sm text-gray-900">{attempt.attempt_number ?? index + 1}</td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {submittedAt ? formatDate(submittedAt) : '—'}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {attempt.is_correct === true
                                ? 'Yes'
                                : attempt.is_correct === false
                                  ? 'No'
                                  : 'Unknown'}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {typeof attempt.time_spent_seconds === 'number'
                                ? attempt.time_spent_seconds
                                : '—'}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              <pre className="max-h-40 overflow-y-auto whitespace-pre-wrap break-words rounded bg-gray-50 p-2 text-xs text-gray-700">
                                {serializedAnswer}
                              </pre>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
