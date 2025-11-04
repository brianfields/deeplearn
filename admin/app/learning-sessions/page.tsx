/**
 * Learning Sessions List Page
 *
 * Presents the admin view of learner sessions with detailed answers.
 */

'use client';

import { LearningSessionsList } from '@/modules/admin/components/learning-sessions/LearningSessionsList';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';
import { useLearningSessions } from '@/modules/admin/queries';
import { useLearningSessionFilters } from '@/modules/admin/store';

export default function LearningSessionsPage() {
  const filters = useLearningSessionFilters();
  const { refetch, isLoading } = useLearningSessions(filters);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Learning Sessions"
        description="Review learner progress and inspect how exercises were answered during each session."
        onReload={() => refetch()}
        isReloading={isLoading}
      />

      <LearningSessionsList />
    </div>
  );
}
