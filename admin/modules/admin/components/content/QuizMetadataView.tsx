import type { QuizMetadata } from '@/modules/admin/models';

interface QuizMetadataViewProps {
  metadata: QuizMetadata;
}

const renderDistribution = (label: string, target: Record<string, number>, actual: Record<string, number>): JSX.Element => {
  const keys = Array.from(new Set([...Object.keys(target), ...Object.keys(actual)]));
  if (keys.length === 0) {
    return (
      <div>
        <h4 className="text-sm font-semibold text-gray-900">{label}</h4>
        <p className="text-sm text-gray-500">No data available.</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-900">{label}</h4>
      <table className="mt-2 min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Target %</th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Actual %</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {keys.map((key) => (
            <tr key={key}>
              <td className="px-3 py-2 text-gray-700">{key}</td>
              <td className="px-3 py-2 text-gray-700">{Math.round((target[key] ?? 0) * 100)}%</td>
              <td className="px-3 py-2 text-gray-700">{Math.round((actual[key] ?? 0) * 100)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const renderList = (label: string, values: string[]): JSX.Element => {
  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-900">{label}</h4>
      {values.length > 0 ? (
        <ul className="mt-2 list-disc list-inside text-sm text-gray-700 space-y-1">
          {values.map((value, idx) => (
            <li key={`${label}-${idx}`}>{value}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-gray-500">No items recorded.</p>
      )}
    </div>
  );
};

export function QuizMetadataView({ metadata }: QuizMetadataViewProps): JSX.Element {
  const coverageByLOEntries = Object.entries(metadata.coverage_by_LO ?? {});
  const coverageByConceptEntries = Object.entries(metadata.coverage_by_concept ?? {});

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Quiz Metadata</h3>
        <p className="text-sm text-gray-600">Insights captured during quiz assembly for quality review.</p>
      </div>
      <div className="px-6 py-6 space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          {renderDistribution('Difficulty Distribution', metadata.difficulty_distribution_target, metadata.difficulty_distribution_actual)}
          {renderDistribution('Cognitive Mix', metadata.cognitive_mix_target, metadata.cognitive_mix_actual)}
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold text-gray-900">Learning Objective Coverage</h4>
            {coverageByLOEntries.length > 0 ? (
              <table className="mt-2 min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Learning Objective</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Exercises</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Concepts</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {coverageByLOEntries.map(([loId, coverage]) => (
                    <tr key={loId}>
                      <td className="px-3 py-2 text-gray-700">{loId}</td>
                      <td className="px-3 py-2 text-gray-700">{coverage.exercise_ids.join(', ') || '—'}</td>
                      <td className="px-3 py-2 text-gray-700">{coverage.concepts.join(', ') || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-gray-500 mt-2">No learning objective coverage recorded.</p>
            )}
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-900">Concept Coverage</h4>
            {coverageByConceptEntries.length > 0 ? (
              <table className="mt-2 min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Concept</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Exercises</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Types</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {coverageByConceptEntries.map(([conceptId, coverage]) => (
                    <tr key={conceptId}>
                      <td className="px-3 py-2 text-gray-700">{conceptId}</td>
                      <td className="px-3 py-2 text-gray-700">{coverage.exercise_ids.join(', ') || '—'}</td>
                      <td className="px-3 py-2 text-gray-700">{coverage.types.join(', ') || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-gray-500 mt-2">No concept coverage recorded.</p>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {renderList('Normalizations Applied', metadata.normalizations_applied)}
          {renderList('Selection Rationale', metadata.selection_rationale)}
          {renderList('Gaps Identified', metadata.gaps_identified)}
        </div>
      </div>
    </div>
  );
}
