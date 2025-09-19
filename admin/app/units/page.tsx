/**
 * Units List Page
 *
 * Browse units with lesson counts.
 */

'use client';

import Link from 'next/link';
import { useUnits } from '@/modules/admin/queries';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';

export default function UnitsPage() {
  const { data: units, isLoading, error, refetch } = useUnits();

  if (isLoading) return <LoadingSpinner size="lg" text="Loading units..." />;
  if (error)
    return (
      <ErrorMessage message="Failed to load units." onRetry={() => refetch()} />
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Units</h1>
        <p className="text-gray-600 mt-2">Browse learning units and their lessons</p>
      </div>

      <div className="bg-white shadow rounded-lg">
        {(!units || units.length === 0) ? (
          <div className="px-6 py-12 text-center text-gray-600">No units found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
            {units.map((u) => (
              <Link key={u.id} href={`/units/${u.id}`} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-lg font-medium text-blue-600 hover:text-blue-500 line-clamp-2">{u.title}</div>
                    {u.description && (
                      <p className="mt-1 text-sm text-gray-600 line-clamp-2">{u.description}</p>
                    )}
                    <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        {u.difficulty}
                      </span>
                      <span className="text-xs text-gray-400">{u.lesson_count} lessons</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
