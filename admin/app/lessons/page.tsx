/**
 * Lessons List Page
 *
 * Shows paginated list of lessons with search and filtering.
 */

import { LessonsList } from '@/modules/admin/components/lessons/LessonsList';

export default function LessonsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Lessons</h1>
        <p className="text-gray-600 mt-2">
          Browse lesson catalog and view detailed lesson packages
        </p>
      </div>

      <LessonsList />
    </div>
  );
}
