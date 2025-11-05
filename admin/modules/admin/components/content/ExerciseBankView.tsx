import { useMemo, useState } from 'react';
import type { LessonExercise } from '@/modules/admin/models';

interface ExerciseBankViewProps {
  exercises: LessonExercise[];
  quizExerciseIds: string[];
}

type FilterValue<T extends string> = T | 'all';

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
};

const badgeClass = (category: string): string => {
  if (category === 'transfer') {
    return 'bg-purple-100 text-purple-800';
  }
  return 'bg-blue-100 text-blue-800';
};

const difficultyBadgeClass = (difficulty: string): string => {
  switch (difficulty) {
    case 'easy':
      return 'bg-green-100 text-green-800';
    case 'hard':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-amber-100 text-amber-800';
  }
};

export function ExerciseBankView({ exercises, quizExerciseIds }: ExerciseBankViewProps): JSX.Element {
  const [categoryFilter, setCategoryFilter] = useState<FilterValue<'comprehension' | 'transfer'>>('all');
  const [cognitiveFilter, setCognitiveFilter] = useState<FilterValue<'Recall' | 'Comprehension' | 'Application' | 'Transfer'>>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<FilterValue<'easy' | 'medium' | 'hard'>>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const quizSet = useMemo(() => new Set(quizExerciseIds), [quizExerciseIds]);

  const cognitiveLevels = useMemo(() => {
    const unique = new Set<string>();
    exercises.forEach((exercise) => unique.add(exercise.cognitive_level));
    return Array.from(unique.values());
  }, [exercises]);

  const filteredExercises = useMemo(() => {
    return exercises.filter((exercise) => {
      if (categoryFilter !== 'all' && exercise.exercise_category !== categoryFilter) {
        return false;
      }
      if (cognitiveFilter !== 'all' && exercise.cognitive_level !== cognitiveFilter) {
        return false;
      }
      if (difficultyFilter !== 'all' && exercise.difficulty !== difficultyFilter) {
        return false;
      }
      return true;
    });
  }, [exercises, categoryFilter, cognitiveFilter, difficultyFilter]);

  if (!exercises || exercises.length === 0) {
    return (
      <div className="bg-white rounded border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
        Exercise bank is empty for this lesson.
      </div>
    );
  }

  const toggleExpanded = (exerciseId: string): void => {
    setExpandedId(expandedId === exerciseId ? null : exerciseId);
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Exercise Bank</h3>
        <p className="text-sm text-gray-600">Review all generated exercises and inspect alignment metadata.</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value as FilterValue<'comprehension' | 'transfer'>)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All Categories</option>
            <option value="comprehension">Comprehension</option>
            <option value="transfer">Transfer</option>
          </select>
          <select
            value={cognitiveFilter}
            onChange={(event) => setCognitiveFilter(event.target.value as FilterValue<'Recall' | 'Comprehension' | 'Application' | 'Transfer'>)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All Cognitive Levels</option>
            {cognitiveLevels.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
          <select
            value={difficultyFilter}
            onChange={(event) => setDifficultyFilter(event.target.value as FilterValue<'easy' | 'medium' | 'hard'>)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
      </div>
      <div className="divide-y divide-gray-200">
        {filteredExercises.map((exercise, index) => {
          const isExpanded = expandedId === exercise.id;
          const inQuiz = quizSet.has(exercise.id);
          const isMcq = exercise.exercise_type === 'mcq';

          return (
            <div key={exercise.id} className="px-6 py-4">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-900">{index + 1}. {exercise.stem}</span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${badgeClass(exercise.exercise_category)}`}>
                      {exercise.exercise_category.charAt(0).toUpperCase() + exercise.exercise_category.slice(1)}
                    </span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${difficultyBadgeClass(exercise.difficulty)}`}>
                      Difficulty: {DIFFICULTY_LABELS[exercise.difficulty] ?? exercise.difficulty}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Cognitive: {exercise.cognitive_level}
                    </span>
                    {inQuiz && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                        In Quiz
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-600">
                    <span className="font-semibold">Aligned LO:</span> {exercise.aligned_learning_objective}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => toggleExpanded(exercise.id)}
                  className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                >
                  {isExpanded ? 'Hide details' : 'View details'}
                </button>
              </div>

              {isExpanded && (
                <div className="mt-4 space-y-4 text-sm text-gray-700">
                  {isMcq ? (
                    <div className="space-y-2">
                      <div className="font-semibold text-gray-900">Answer Options</div>
                      <ul className="space-y-2">
                        {exercise.options.map((option) => (
                          <li key={option.id} className="border border-gray-200 rounded p-2">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-gray-900">
                                {option.label}. {option.text}
                              </span>
                              {option.rationale_wrong && (
                                <span className="text-xs text-gray-500">{option.rationale_wrong}</span>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                      {exercise.answer_key && (
                        <div className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-2">
                          <span className="font-semibold">Correct answer:</span> {exercise.answer_key.label}
                          {exercise.answer_key.rationale_right && (
                            <span className="ml-2">{exercise.answer_key.rationale_right}</span>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div>
                        <div className="font-semibold text-gray-900">Canonical Answer</div>
                        <div>{exercise.canonical_answer}</div>
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">Acceptable Answers</div>
                        {exercise.acceptable_answers.length > 0 ? (
                          <ul className="list-disc list-inside space-y-1">
                            {exercise.acceptable_answers.map((answer, idx) => (
                              <li key={`${exercise.id}-acceptable-${idx}`}>{answer}</li>
                            ))}
                          </ul>
                        ) : (
                          <div className="text-gray-500">None provided</div>
                        )}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">Common Misconceptions</div>
                        {exercise.wrong_answers.length > 0 ? (
                          <ul className="space-y-2">
                            {exercise.wrong_answers.map((wrong, idx) => (
                              <li key={`${exercise.id}-wrong-${idx}`} className="border border-amber-200 bg-amber-50 rounded p-2">
                                <div className="font-medium text-gray-900">{wrong.answer}</div>
                                <div className="text-xs text-gray-700">{wrong.rationale_wrong}</div>
                                {wrong.misconception_ids.length > 0 && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    Misconceptions: {wrong.misconception_ids.join(', ')}
                                  </div>
                                )}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <div className="text-gray-500">No specific misconceptions provided.</div>
                        )}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">Correct Answer Feedback</div>
                        <div>{exercise.explanation_correct}</div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
