/**
 * Lesson Package Viewer Component
 *
 * Beautiful, structured display of lesson package content including:
 * - Learning objectives
 * - Glossary terms
 * - Didactic content
 * - MCQ items with answer keys
 * - Misconceptions and confusables
 */

'use client';

import { useState } from 'react';
import { JSONViewer } from '../shared/JSONViewer';
import { cn } from '@/lib/utils';
import type { LessonPackage, MCQExercise } from '../../models';

interface LessonPackageViewerProps {
  package: LessonPackage;
}

export function LessonPackageViewer({ package: pkg }: LessonPackageViewerProps) {
  const [activeSection, setActiveSection] = useState<string>('objectives');
  const [showAnswers, setShowAnswers] = useState(false);

  const sections = [
    { id: 'objectives', name: 'Learning Objectives', icon: '🎯' },
    { id: 'glossary', name: 'Glossary', icon: '📚' },
    { id: 'mini_lesson', name: 'Mini Lesson', icon: '📖' },
    { id: 'exercises', name: 'Exercises', icon: '❓' },
    { id: 'misconceptions', name: 'Misconceptions', icon: '⚠️' },
    { id: 'confusables', name: 'Confusables', icon: '🔄' },
  ];

  return (
    <div className="space-y-6">
      {/* Package Meta Information */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Package Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <span className="text-sm font-medium text-gray-600">Title:</span>
            <p className="text-gray-900">{pkg.meta.title}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Domain:</span>
            <p className="text-gray-900">{pkg.meta.domain}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">User Level:</span>
            <p className="text-gray-900">{pkg.meta.user_level}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Schema Version:</span>
            <p className="text-gray-900">v{pkg.meta.package_schema_version}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Content Version:</span>
            <p className="text-gray-900">v{pkg.meta.content_version}</p>
          </div>
        </div>

        {/* Length Budgets */}
        <div className="mt-4 p-4 bg-white rounded-lg border">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Length Budgets</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Stem:</span>
              <span className="ml-2 font-medium">{pkg.meta.length_budgets.stem_max_words} words</span>
            </div>
            <div>
              <span className="text-gray-600">Vignette:</span>
              <span className="ml-2 font-medium">{pkg.meta.length_budgets.vignette_max_words} words</span>
            </div>
            <div>
              <span className="text-gray-600">Option:</span>
              <span className="ml-2 font-medium">{pkg.meta.length_budgets.option_max_words} words</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={cn(
                'py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap',
                activeSection === section.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              )}
            >
              <span className="mr-2">{section.icon}</span>
              {section.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Section Content */}
      <div className="min-h-96">
        {activeSection === 'objectives' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Learning Objectives</h3>
            <div className="grid gap-4">
              {pkg.objectives.map((objective, index) => (
                <div key={objective.id} className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-900">{objective.text}</p>
                      {objective.bloom_level && (
                        <span className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Bloom Level: {objective.bloom_level}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'glossary' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Glossary Terms</h3>
            <div className="space-y-4">
              {Object.entries(pkg.glossary).map(([objectiveId, terms]) => (
                <div key={objectiveId} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-3">Objective: {objectiveId}</h4>
                  <div className="space-y-3">
                    {terms.map((term) => (
                      <div key={term.id} className="bg-white rounded-lg p-3 border">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h5 className="font-medium text-gray-900">{term.term}</h5>
                            <p className="mt-1 text-gray-700">{term.definition}</p>
                            {term.relation_to_core && (
                              <p className="mt-2 text-sm text-blue-600">
                                <strong>Relation to core:</strong> {term.relation_to_core}
                              </p>
                            )}
                            {term.common_confusion && (
                              <p className="mt-1 text-sm text-orange-600">
                                <strong>Common confusion:</strong> {term.common_confusion}
                              </p>
                            )}
                            {term.micro_check && (
                              <p className="mt-1 text-sm text-green-600">
                                <strong>Micro check:</strong> {term.micro_check}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'mini_lesson' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Mini Lesson</h3>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="font-medium text-purple-900 mb-3">Lesson Explanation (Markdown)</h4>
              <div className="bg-white rounded-lg p-4 border whitespace-pre-wrap break-words">
                {pkg.mini_lesson || 'No mini lesson provided.'}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'exercises' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Exercises</h3>
              <button
                onClick={() => setShowAnswers(!showAnswers)}
                className={cn(
                  'px-3 py-1 rounded-md text-sm font-medium',
                  showAnswers
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                )}
              >
                {showAnswers ? 'Hide Answers' : 'Show Answers'}
              </button>
            </div>

            <div className="space-y-6">
              {pkg.exercises.map((exercise, index) => (
                <div key={exercise.id} className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-gray-600 text-white rounded-full flex items-center justify-center font-medium">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-4 mb-3">
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded font-medium">
                          {exercise.exercise_type.toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-600">LO: {exercise.lo_id}</span>
                        {exercise.cognitive_level && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {exercise.cognitive_level}
                          </span>
                        )}
                        {exercise.estimated_difficulty && (
                          <span className={cn(
                            'px-2 py-1 text-xs rounded',
                            exercise.estimated_difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                            exercise.estimated_difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          )}>
                            {exercise.estimated_difficulty}
                          </span>
                        )}
                      </div>

                      {exercise.exercise_type === 'mcq' && (
                        <>
                          <div className="mb-4">
                            <strong className="text-gray-900">Question:</strong>
                            <p className="mt-1 text-gray-700">{(exercise as MCQExercise).stem}</p>
                          </div>

                          <div className="space-y-2">
                            {((exercise as MCQExercise).options || []).map((option) => (
                              <div
                                key={option.id}
                                className={cn(
                                  'p-3 rounded border',
                                  showAnswers && option.label === (exercise as MCQExercise).answer_key.label
                                    ? 'bg-green-100 border-green-300'
                                    : 'bg-white border-gray-200'
                                )}
                              >
                                <div className="flex items-start space-x-3">
                                  <span className="flex-shrink-0 w-6 h-6 bg-gray-100 text-gray-700 rounded-full flex items-center justify-center text-sm font-medium">
                                    {option.label}
                                  </span>
                                  <div className="flex-1">
                                    <p className="text-gray-900">{option.text}</p>
                                    {showAnswers && option.rationale_wrong && (
                                      <p className="mt-1 text-sm text-red-600">
                                        <strong>Why wrong:</strong> {option.rationale_wrong}
                                      </p>
                                    )}
                                  </div>
                                  {showAnswers && option.label === (exercise as MCQExercise).answer_key.label && (
                                    <span className="text-green-600">✓</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </>
                      )}

                      {exercise.exercise_type !== 'mcq' && (
                        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
                          <p className="text-blue-800">
                            <strong>Exercise Type:</strong> {exercise.exercise_type}
                          </p>
                          <p className="text-sm text-blue-600 mt-1">
                            This exercise type is not yet fully supported in the admin viewer.
                          </p>
                        </div>
                      )}

                      {exercise.misconceptions_used.length > 0 && (
                        <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded">
                          <strong className="text-orange-800">Misconceptions addressed:</strong>
                          <p className="mt-1 text-sm text-gray-700">
                            {exercise.misconceptions_used.join(', ')}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'misconceptions' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Misconceptions</h3>
            <div className="grid gap-4">
              {pkg.misconceptions.map((misconception, index) => (
                <div key={index} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  {Object.entries(misconception).map(([term, description]) => (
                    <div key={term}>
                      <h4 className="font-medium text-orange-900">{term}</h4>
                      <p className="mt-1 text-gray-700">{description}</p>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'confusables' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Confusables</h3>
            <div className="grid gap-4">
              {pkg.confusables.map((confusable, index) => (
                <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4">
                  {Object.entries(confusable).map(([term, description]) => (
                    <div key={term}>
                      <h4 className="font-medium text-red-900">{term}</h4>
                      <p className="mt-1 text-gray-700">{description}</p>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
