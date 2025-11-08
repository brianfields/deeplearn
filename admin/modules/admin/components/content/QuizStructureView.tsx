import { useMemo, useState } from 'react';
import type { LessonExercise } from '@/modules/admin/models';

interface QuizStructureViewProps {
  quizIds: string[];
  exerciseBank: LessonExercise[];
}

export function QuizStructureView({ quizIds, exerciseBank }: QuizStructureViewProps): JSX.Element {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const exerciseMap = useMemo(() => {
    return new Map<string, LessonExercise>(exerciseBank.map((exercise) => [exercise.id, exercise]));
  }, [exerciseBank]);

  if (!quizIds || quizIds.length === 0) {
    return (
      <div className="bg-white rounded border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
        Quiz assembly did not select any exercises.
      </div>
    );
  }

  const toggleExpanded = (exerciseId: string): void => {
    setExpandedId(expandedId === exerciseId ? null : exerciseId);
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Quiz Structure</h3>
        <p className="text-sm text-gray-600">Ordered list of exercises presented to learners during the quiz.</p>
      </div>
      <ol className="divide-y divide-gray-200">
        {quizIds.map((exerciseId, index) => {
          const exercise = exerciseMap.get(exerciseId);
          const isExpanded = expandedId === exerciseId;

          if (!exercise) {
            return (
              <li key={exerciseId} className="px-6 py-4 text-sm text-red-600">
                Missing exercise metadata for ID {exerciseId}
              </li>
            );
          }

          const isMcq = exercise.exercise_type === 'mcq';

          return (
            <li key={exerciseId} className="px-6 py-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-gray-900">
                    {index + 1}. {exercise.stem}
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-medium">
                      {exercise.exercise_type === 'mcq' ? 'Multiple Choice' : 'Short Answer'}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-medium">
                      {exercise.exercise_category.charAt(0).toUpperCase() + exercise.exercise_category.slice(1)}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-100 text-gray-800 font-medium">
                      Cognitive: {exercise.cognitive_level}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">
                      Difficulty: {exercise.difficulty}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
                      LO: {exercise.aligned_learning_objective}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => toggleExpanded(exerciseId)}
                  className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                >
                  {isExpanded ? 'Hide details' : 'View details'}
                </button>
              </div>
              {isExpanded && (
                <div className="mt-3 text-sm text-gray-700 space-y-3">
                  {isMcq ? (
                    <div className="space-y-2">
                      <div className="font-semibold text-gray-900">Options</div>
                      <ul className="space-y-1">
                        {exercise.options.map((option) => (
                          <li key={option.id} className="border border-gray-200 rounded p-2">
                            <span className="font-medium text-gray-900">{option.label}.</span> {option.text}
                            {option.rationale_wrong && (
                              <div className="text-xs text-gray-500 mt-1">{option.rationale_wrong}</div>
                            )}
                          </li>
                        ))}
                      </ul>
                      {exercise.answer_key && (
                        <div className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-2">
                          Correct answer: {exercise.answer_key.label}
                          {exercise.answer_key.rationale_right && (
                            <span className="ml-2">{exercise.answer_key.rationale_right}</span>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div>
                        <span className="font-semibold text-gray-900">Canonical Answer:</span>{' '}
                        {exercise.canonical_answer}
                      </div>
                      <div>
                        <span className="font-semibold text-gray-900">Acceptable Answers:</span>
                        {exercise.acceptable_answers.length > 0 ? (
                          <ul className="list-disc list-inside space-y-1">
                            {exercise.acceptable_answers.map((answer, idx) => (
                              <li key={`${exercise.id}-acceptable-${idx}`}>{answer}</li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-gray-500"> None listed.</span>
                        )}
                      </div>
                      <div>
                        <span className="font-semibold text-gray-900">Misconception Feedback:</span>
                        {exercise.wrong_answers.length > 0 ? (
                          <ul className="space-y-1 mt-1">
                            {exercise.wrong_answers.map((wrong, idx) => (
                              <li key={`${exercise.id}-wrong-${idx}`} className="border border-amber-200 bg-amber-50 rounded p-2">
                                <div className="font-medium text-gray-900">{wrong.answer}</div>
                                <div className="text-xs text-gray-700">{wrong.rationale_wrong}</div>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-gray-500"> No specific wrong answers provided.</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
