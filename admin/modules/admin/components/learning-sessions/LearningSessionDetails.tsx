/**
 * Learning Session Details Component
 *
 * Displays per-exercise answers for a learning session when expanded in the table.
 */

'use client';

import type { LearningSessionSummary } from '@/modules/admin/models';
import { formatDate } from '@/lib/utils';

interface LearningSessionDetailsProps {
  session: LearningSessionSummary;
}

export function LearningSessionDetails({ session }: LearningSessionDetailsProps) {
  const exerciseAnswers = (session.session_data?.exercise_answers ?? {}) as Record<string, any>;
  const exerciseIds = Object.keys(exerciseAnswers);

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
