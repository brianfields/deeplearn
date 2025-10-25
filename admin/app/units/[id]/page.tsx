/**
 * Unit Details Page
 *
 * Shows unit metadata and ordered lessons.
 */

'use client';

import Link from 'next/link';
import { useUnit, useUnitFlowRuns, useRetryUnit } from '@/modules/admin/queries';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';
import { ReloadButton } from '@/modules/admin/components/shared/ReloadButton';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { formatDate, formatExecutionTime, formatTokens, formatCost } from '@/lib/utils';

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

export default function UnitDetailsPage({ params }: UnitDetailsPageProps) {
  const { data: unit, isLoading, error, refetch } = useUnit(params.id);
  const {
    data: flowRuns,
    isLoading: flowsLoading,
    error: flowsError,
    refetch: refetchFlows,
  } = useUnitFlowRuns(params.id);
  const retryUnit = useRetryUnit();

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

  const unitFlowRuns = flowRuns ?? unit.flow_runs ?? [];
  const isRetrying = retryUnit.isPending;

  const handleRetry = () => {
    if (retryUnit.isPending) {
      return;
    }
    retryUnit.mutate(unit.id, {
      onSuccess: () => {
        void refetch();
        void refetchFlows();
      },
    });
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
            void refetchFlows();
          }}
          isLoading={isLoading || flowsLoading || isRetrying}
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
            <Link href={`/tasks?taskId=${unit.arq_task_id}`} className="mt-2 inline-block text-xs text-blue-600 hover:text-blue-500">
              View creation task →
            </Link>
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
          <p className="text-xs uppercase text-gray-500">Flow runs</p>
          <p className="mt-2 text-sm text-gray-700">{unitFlowRuns.length} associated flow runs</p>
          <p className="mt-2 text-xs text-gray-500">Creation started {formatDate(unit.created_at)}</p>
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

      <div className="bg-white rounded-lg shadow">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Associated flow runs</h2>
            <p className="text-sm text-gray-600">Background flow executions linked to this unit.</p>
          </div>
          <ReloadButton onReload={() => refetchFlows()} isLoading={flowsLoading} label="Reload flows" />
        </div>
        {flowsLoading && unitFlowRuns.length === 0 && (
          <div className="px-6 py-6">
            <LoadingSpinner size="sm" text="Loading flow runs…" />
          </div>
        )}
        {flowsError && (
          <ErrorMessage
            message="Failed to load flow runs for this unit."
            details={flowsError instanceof Error ? flowsError.message : undefined}
            onRetry={() => refetchFlows()}
          />
        )}
        {!flowsLoading && unitFlowRuns.length === 0 && (
          <div className="px-6 py-6 text-sm text-gray-500">No flow runs recorded yet.</div>
        )}
        {unitFlowRuns.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-6 py-3 text-left font-medium">Flow</th>
                  <th className="px-6 py-3 text-left font-medium">Status</th>
                  <th className="px-6 py-3 text-left font-medium">Started</th>
                  <th className="px-6 py-3 text-left font-medium">Duration</th>
                  <th className="px-6 py-3 text-left font-medium">Tokens</th>
                  <th className="px-6 py-3 text-left font-medium">Cost</th>
                  <th className="px-6 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white text-sm text-gray-700">
                {unitFlowRuns.map((run) => (
                  <tr key={run.id}>
                    <td className="px-6 py-3">
                      <div className="font-medium text-gray-900">{run.flow_name}</div>
                      <div className="text-xs text-gray-500">{run.execution_mode}</div>
                    </td>
                    <td className="px-6 py-3">
                      <StatusBadge status={run.status} size="sm" />
                    </td>
                    <td className="px-6 py-3">{formatDate(run.started_at)}</td>
                    <td className="px-6 py-3">{formatExecutionTime(run.execution_time_ms)}</td>
                    <td className="px-6 py-3">{formatTokens(run.total_tokens)}</td>
                    <td className="px-6 py-3">{formatCost(run.total_cost)}</td>
                    <td className="px-6 py-3 text-right">
                      <Link href={`/flows/${run.id}`} className="text-blue-600 hover:text-blue-500">
                        View flow
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
