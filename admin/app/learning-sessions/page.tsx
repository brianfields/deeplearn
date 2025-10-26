/**
 * Learning Sessions List Page
 *
 * Presents the admin view of learner sessions with detailed answers.
 */

import { LearningSessionsList } from '@/modules/admin/components/learning-sessions/LearningSessionsList';

export default function LearningSessionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Learning Sessions</h1>
        <p className="mt-2 text-gray-600">
          Review learner progress and inspect how exercises were answered during each session.
        </p>
      </div>

      <LearningSessionsList />
    </div>
  );
}
