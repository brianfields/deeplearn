/**
 * Unit Details Page
 *
 * Shows unit metadata and ordered lessons.
 */

'use client';

import Link from 'next/link';
import { useUnit } from '@/modules/admin/queries';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';

interface UnitDetailsPageProps {
  params: { id: string };
}

export default function UnitDetailsPage({ params }: UnitDetailsPageProps) {
  const { data: unit, isLoading, error, refetch } = useUnit(params.id);

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/units" className="text-sm text-gray-500 hover:text-gray-700">← Back to units</Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">{unit.title}</h1>
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
        <button onClick={() => refetch()} className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          <span>Reload</span>
        </button>
      </div>

      {/* Unit-level Learning Objectives & Source Material */}
      {(unit.learning_objectives || unit.source_material) && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Unit Overview</h2>
            <p className="text-sm text-gray-600">Learning objectives and source material</p>
          </div>
          <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-6">
            {unit.learning_objectives && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Learning Objectives</h3>
                <ul className="list-disc list-inside space-y-1">
                  {unit.learning_objectives.map((lo, idx) => (
                    <li key={idx} className="text-sm text-gray-700">{lo}</li>
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

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Lessons</h2>
          <p className="text-sm text-gray-600">Ordered lessons in this unit</p>
        </div>
        <ul className="divide-y divide-gray-200">
          {unit.lessons.map((l, idx) => (
            <li key={l.id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="w-8 h-8 inline-flex items-center justify-center rounded-full bg-gray-100 text-gray-700 text-sm font-medium">{idx + 1}</span>
                <div>
                  <Link href={`/lessons/${l.id}`} className="text-blue-600 hover:text-blue-800 font-medium">{l.title}</Link>
                  <div className="mt-1 text-sm text-gray-500">{l.learner_level ?? 'beginner'} • {l.exercise_count} exercises</div>
                </div>
              </div>
              <Link href={`/lessons/${l.id}`} className="text-sm text-blue-600 hover:text-blue-800">View lesson →</Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
