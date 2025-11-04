/**
 * Units Page
 *
 * Displays a table of units with clickable rows linking to detail pages.
 */

'use client';

import { useMemo, useState } from 'react';
import { useUnits } from '@/modules/admin/queries';
import { DetailViewTable, type DetailViewTableColumn } from '@/modules/admin/components/shared/DetailViewTable';
import { StatusBadge } from '@/modules/admin/components/shared/StatusBadge';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';
import { formatDate } from '@/lib/utils';
import type { UnitSummary } from '@/modules/admin/models';

export default function UnitsPage(): JSX.Element {
  const { data: allUnits, isLoading, error, refetch } = useUnits();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const PAGE_SIZE_OPTIONS = [10, 25, 50];

  // Client-side pagination
  const { units, totalCount, totalPages } = useMemo(() => {
    const all = allUnits ?? [];
    const total = all.length;
    const pages = Math.max(1, Math.ceil(total / pageSize));
    const startIdx = (page - 1) * pageSize;
    const endIdx = startIdx + pageSize;
    const paginated = all.slice(startIdx, endIdx);

    return {
      units: paginated,
      totalCount: total,
      totalPages: pages,
    };
  }, [allUnits, page, pageSize]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reset to first page when changing page size
  };

  const emptyIcon = (
    <svg
      className="h-12 w-12 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 6.253v13m0-13C6.5 6.253 2 10.753 2 16.253s4.5 10 10 10 10-4.5 10-10S17.5 6.253 12 6.253z"
      />
    </svg>
  );

  const columns: DetailViewTableColumn<UnitSummary>[] = [
    {
      key: 'title',
      label: 'Unit Title',
      render: (unit) => (
        <div>
          <div className="text-sm font-medium text-gray-900">{unit.title}</div>
          {unit.description && (
            <div className="mt-1 text-xs text-gray-500 line-clamp-2">{unit.description}</div>
          )}
        </div>
      ),
    },
    {
      key: 'learner_level',
      label: 'Level',
      render: (unit) => (
        <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
          {unit.learner_level}
        </span>
      ),
    },
    {
      key: 'lessons',
      label: 'Lessons',
      render: (unit) => (
        <div className="flex flex-col">
          <span>{unit.lesson_count} lessons</span>
          {unit.target_lesson_count !== null && (
            <span className="text-xs text-gray-500">Target: {unit.target_lesson_count}</span>
          )}
        </div>
      ),
    },
    {
      key: 'flow_type',
      label: 'Type',
      render: (unit) => (
        <span className="inline-flex items-center gap-1">
          {unit.flow_type === 'fast' ? (
            <span className="inline-flex items-center rounded-full bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700">
              Fast flow
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-gray-50 px-2 py-1 text-xs font-medium text-gray-700">
              Standard
            </span>
          )}
          {unit.generated_from_topic && (
            <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">
              Topic-generated
            </span>
          )}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (unit) => unit.status ? <StatusBadge status={unit.status} size="sm" /> : <span className="text-gray-500">—</span>,
    },
    {
      key: 'updated_at',
      label: 'Updated',
      render: (unit) => unit.updated_at ? formatDate(unit.updated_at) : '—',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Units"
        description="Browse units and click to view details."
        onReload={() => refetch()}
        isReloading={isLoading}
      />

      <DetailViewTable
        data={units}
        columns={columns}
        getRowId={(unit) => unit.id}
        getDetailHref={(unit) => `/units/${unit.id}`}
        isLoading={isLoading}
        error={error}
        emptyMessage="No units available."
        emptyIcon={emptyIcon}
        onRetry={() => refetch()}
        pagination={{
          currentPage: page,
          totalPages,
          totalCount,
          pageSize,
          hasNext: page < totalPages,
        }}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        pageOptions={PAGE_SIZE_OPTIONS}
      />
    </div>
  );
}
