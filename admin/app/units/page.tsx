/**
 * Units Page
 *
 * Accordion view of units with inline lesson summaries.
 */

'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useUnit, useUnits } from '@/modules/admin/queries';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';
import { ReloadButton } from '@/modules/admin/components/shared/ReloadButton';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { formatDate } from '@/lib/utils';
import type { UnitSummary } from '@/modules/admin/models';

interface UnitAccordionItemProps {
  unit: UnitSummary;
  isExpanded: boolean;
  onToggle: () => void;
}

function UnitAccordionItem({ unit, isExpanded, onToggle }: UnitAccordionItemProps) {
  const {
    data: detail,
    isLoading,
    error,
    refetch,
  } = useUnit(unit.id, { enabled: isExpanded });

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-5 py-4 text-left"
        aria-expanded={isExpanded}
      >
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900">{unit.title}</h3>
            {unit.status && <StatusBadge status={unit.status} size="sm" />}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span>{unit.learner_level}</span>
            <span>Lessons: {unit.lesson_count}</span>
            {unit.target_lesson_count !== null && <span>Target: {unit.target_lesson_count}</span>}
            <span>{unit.flow_type === 'fast' ? 'Fast flow' : 'Standard flow'}</span>
            {unit.generated_from_topic && <span>Topic-generated</span>}
          </div>
          <div className="mt-1 text-xs text-gray-400">
            Updated {unit.updated_at ? formatDate(unit.updated_at) : '—'}
          </div>
        </div>
        <svg
          className={`h-5 w-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : 'rotate-0'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
      {isExpanded && (
        <div className="border-t border-gray-200 px-5 py-4">
          {isLoading && !detail && <LoadingSpinner size="sm" text="Loading unit…" />}
          {error && (
            <ErrorMessage
              message="Failed to load unit details."
              details={error instanceof Error ? error.message : undefined}
              onRetry={() => refetch()}
            />
          )}
          {detail && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Created:</span> {formatDate(unit.created_at)}
                </div>
                <ReloadButton onReload={() => refetch()} isLoading={isLoading} label="Reload unit" />
              </div>
              {detail.learning_objectives && detail.learning_objectives.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900">Learning objectives</h4>
                  <ul className="mt-2 space-y-3">
                    {detail.learning_objectives.map((objective) => (
                      <li key={objective.id} className="border-l-2 border-blue-200 pl-3">
                        <p className="text-sm font-medium text-gray-900">
                          {objective.title || objective.description || objective.id}
                        </p>
                        {objective.description && (
                          <p className="mt-0.5 text-xs text-gray-600">{objective.description}</p>
                        )}
                        {objective.bloom_level && (
                          <p className="mt-0.5 text-[11px] uppercase tracking-wide text-gray-400">
                            Bloom level: {objective.bloom_level}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div>
                <h4 className="text-sm font-semibold text-gray-900">Lessons</h4>
                <ul className="mt-2 divide-y divide-gray-200 text-sm text-gray-700">
                  {detail.lessons.map((lesson, index) => (
                    <li key={lesson.id} className="py-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{index + 1}. {lesson.title}</p>
                          <p className="text-xs text-gray-500">Level: {lesson.learner_level} • Exercises: {lesson.exercise_count}</p>
                        </div>
                        <Link
                          href={`/units/${detail.id}?lesson=${lesson.id}`}
                          className="text-xs text-blue-600 hover:text-blue-500"
                        >
                          View details
                        </Link>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Link href={`/units/${detail.id}`} className="text-blue-600 hover:text-blue-500">
                  Open full unit →
                </Link>
                {unit.arq_task_id && (
                  <Link href={`/tasks?taskId=${unit.arq_task_id}`} className="text-blue-600 hover:text-blue-500">
                    View task →
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function UnitsPage() {
  const { data: units, isLoading, error, refetch } = useUnits();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleUnit = (unitId: string) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(unitId)) {
        next.delete(unitId);
      } else {
        next.add(unitId);
      }
      return next;
    });
  };

  if (isLoading && !units) {
    return <LoadingSpinner size="lg" text="Loading units…" />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load units."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Units</h1>
          <p className="mt-2 text-gray-600">Expand a unit to view its lessons inline.</p>
        </div>
        <ReloadButton onReload={() => refetch()} isLoading={isLoading} />
      </div>

      <div className="space-y-3">
        {(units ?? []).map((unit) => (
          <UnitAccordionItem
            key={unit.id}
            unit={unit}
            isExpanded={expanded.has(unit.id)}
            onToggle={() => toggleUnit(unit.id)}
          />
        ))}
      </div>
    </div>
  );
}
