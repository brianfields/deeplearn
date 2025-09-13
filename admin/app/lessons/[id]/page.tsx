/**
 * Lesson Details Page
 *
 * Shows detailed information about a specific lesson and its package.
 */

import { LessonDetails } from '@/modules/admin/components/lessons/LessonDetails';

interface LessonDetailsPageProps {
  params: { id: string };
}

export default function LessonDetailsPage({ params }: LessonDetailsPageProps) {
  return (
    <div className="space-y-6">
      <LessonDetails lessonId={params.id} />
    </div>
  );
}
