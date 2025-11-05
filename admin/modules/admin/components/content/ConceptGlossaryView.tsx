import { useState } from 'react';
import type { RefinedConcept } from '@/modules/admin/models';

interface ConceptGlossaryViewProps {
  concepts: RefinedConcept[];
}

const formatDifficultyPotential = (value: Record<string, string> | null): string => {
  if (!value) {
    return '—';
  }

  const entries = Object.entries(value);
  if (entries.length === 0) {
    return '—';
  }

  return entries
    .map(([level, description]) => `${level}: ${description}`)
    .join('; ');
};

const renderList = (items: string[]): JSX.Element => {
  if (!items || items.length === 0) {
    return <span className="text-gray-400">—</span>;
  }

  return (
    <span className="text-gray-700">
      {items.join(', ')}
    </span>
  );
};

export function ConceptGlossaryView({ concepts }: ConceptGlossaryViewProps): JSX.Element {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!concepts || concepts.length === 0) {
    return (
      <div className="bg-white rounded border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
        No concepts were generated for this lesson.
      </div>
    );
  }

  const toggleExpanded = (conceptId: string): void => {
    setExpandedId(expandedId === conceptId ? null : conceptId);
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Concept Glossary</h3>
        <p className="text-sm text-gray-600">
          Review refined concepts with pedagogical metadata used during exercise generation.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Concept
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Definition
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Centrality
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Distinctiveness
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Transferability
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Clarity
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Assessment Potential
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cognitive Domain
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Difficulty Potential
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Canonical Answer
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Plausible Distractors
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Details
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {concepts.map((concept) => {
              const isExpanded = expandedId === concept.id;
              return (
                <tr key={concept.id} className="align-top">
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    <div>{concept.term}</div>
                    {concept.aliases.length > 0 && (
                      <div className="text-xs text-gray-500">Aliases: {concept.aliases.join(', ')}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.definition}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.centrality}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.distinctiveness}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.transferability}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.clarity}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.assessment_potential}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.cognitive_domain}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{formatDifficultyPotential(concept.difficulty_potential)}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{concept.canonical_answer}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{renderList(concept.plausible_distractors)}</td>
                  <td className="px-6 py-4 text-sm text-right">
                    <button
                      type="button"
                      onClick={() => toggleExpanded(concept.id)}
                      className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                    >
                      {isExpanded ? 'Hide' : 'View'}
                    </button>
                    {isExpanded && (
                      <div className="mt-3 space-y-2 text-left">
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Example from source:</span>{' '}
                          {concept.example_from_source ?? '—'}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Aligned LOs:</span>{' '}
                          {renderList(concept.aligned_learning_objectives)}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Accepted phrases:</span>{' '}
                          {renderList(concept.accepted_phrases)}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Misconception note:</span>{' '}
                          {concept.misconception_note ?? '—'}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Contrast with:</span>{' '}
                          {renderList(concept.contrast_with)}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Related concepts:</span>{' '}
                          {renderList(concept.related_concepts)}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Review notes:</span>{' '}
                          {concept.review_notes ?? '—'}
                        </div>
                        <div className="text-xs text-gray-600">
                          <span className="font-semibold">Source reference:</span>{' '}
                          {concept.source_reference ?? '—'}
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
