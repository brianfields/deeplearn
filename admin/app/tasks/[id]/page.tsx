/**
 * Task Detail Page
 *
 * Renders detailed information about a specific background task.
 */

'use client';

import Link from 'next/link';
import { TaskDetails } from '@/modules/admin/components/tasks/TaskDetails';

interface TaskDetailPageProps {
  params: { id: string };
}

export default function TaskDetailPage({ params }: TaskDetailPageProps): JSX.Element {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <Link href="/tasks" className="text-sm text-gray-500 hover:text-gray-700">
          ← Back to tasks
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Task {params.id}</h1>
        <p className="text-gray-600">
          View task status, execution details, and associated flow runs.
        </p>
      </div>

      <TaskDetails taskId={params.id} />
    </div>
  );
}
