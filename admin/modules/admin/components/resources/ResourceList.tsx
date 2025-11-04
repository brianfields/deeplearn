import Link from 'next/link';
import type {
  ResourceSummary,
  ResourceUsageSummary,
} from '@/modules/admin/models';
import { DetailViewTable, type DetailViewTableColumn } from '../shared/DetailViewTable';
import { formatDate } from '@/lib/utils';

const BADGE_BASE_CLASSES =
  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border';

const RESOURCE_TYPE_STYLES: Record<string, string> = {
  generated_source: 'bg-violet-100 text-violet-800 border-violet-200',
  url: 'bg-blue-100 text-blue-800 border-blue-200',
  file_upload: 'bg-slate-100 text-slate-800 border-slate-200',
  file: 'bg-slate-100 text-slate-800 border-slate-200',
  default: 'bg-gray-100 text-gray-700 border-gray-200',
};

type ResourceListItem = ResourceSummary & {
  used_in_units?: ResourceUsageSummary[];
};

interface ResourceListProps {
  readonly resources: ResourceListItem[];
  readonly emptyMessage?: string;
  readonly showUsageColumn?: boolean;
}

const formatFileSize = (value: number | null): string => {
  if (!value || Number.isNaN(value)) {
    return '—';
  }
  const kilobytes = value / 1024;
  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }
  const megabytes = kilobytes / 1024;
  if (megabytes < 1024) {
    return `${megabytes.toFixed(1)} MB`;
  }
  const gigabytes = megabytes / 1024;
  return `${gigabytes.toFixed(1)} GB`;
};

const resourceLabel = (resource: ResourceSummary): string => {
  if (resource.filename) {
    return resource.filename;
  }
  if (resource.source_url) {
    return resource.source_url;
  }
  return resource.id;
};

const normalizePreview = (preview: string): string => {
  if (!preview) {
    return '—';
  }
  const trimmed = preview.trim();
  if (trimmed.length <= 160) {
    return trimmed;
  }
  return `${trimmed.slice(0, 157)}…`;
};

const formatResourceTypeLabel = (value: string): string => {
  if (!value) {
    return 'Unknown';
  }
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

export function ResourceTypeBadge({ resourceType }: { resourceType: string }): JSX.Element {
  const normalized = resourceType?.toLowerCase() ?? 'default';
  const variantClasses = RESOURCE_TYPE_STYLES[normalized] ?? RESOURCE_TYPE_STYLES.default;
  return (
    <span
      data-testid={`resource-type-${normalized}`}
      className={`${BADGE_BASE_CLASSES} ${variantClasses}`}
    >
      {formatResourceTypeLabel(resourceType)}
    </span>
  );
}

export function ResourceList({
  resources,
  emptyMessage,
  showUsageColumn = false,
}: ResourceListProps): JSX.Element {
  if (!resources || resources.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        {emptyMessage ?? 'No resources available.'}
      </p>
    );
  }

  const columns: DetailViewTableColumn<ResourceListItem>[] = [
    {
      key: 'resource',
      label: 'Resource',
      render: (resource) => (
        <div>
          <div className="font-medium text-gray-900">{resourceLabel(resource)}</div>
          <div className="mt-1">
            <ResourceTypeBadge resourceType={resource.resource_type} />
          </div>
          {resource.source_url && (
            <div className="mt-1 text-xs">
              <a
                href={resource.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:text-blue-500"
              >
                Open source →
              </a>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'created_at',
      label: 'Added',
      render: (resource) => formatDate(resource.created_at),
    },
    {
      key: 'file_size',
      label: 'Size',
      render: (resource) => formatFileSize(resource.file_size ?? null),
    },
    {
      key: 'preview',
      label: 'Preview',
      render: (resource) => (
        <div className="max-w-xs whitespace-pre-wrap break-words text-sm text-gray-700">
          {normalizePreview(resource.preview_text)}
        </div>
      ),
    },
    ...(showUsageColumn
      ? [
          {
            key: 'usage',
            label: 'Used In Units',
            render: (resource: ResourceListItem) =>
              resource.used_in_units && resource.used_in_units.length > 0 ? (
                <ul className="space-y-1">
                  {resource.used_in_units.map((unit) => (
                    <li key={`${resource.id}-${unit.unit_id}`}>
                      <Link
                        href={`/units/${unit.unit_id}`}
                        className="text-blue-600 hover:text-blue-500"
                      >
                        {unit.unit_title}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="text-gray-500">—</span>
              ),
          } as DetailViewTableColumn<ResourceListItem>,
        ]
      : []),
  ];

  return (
    <DetailViewTable
      data={resources}
      columns={columns}
      getRowId={(resource) => resource.id}
      getDetailHref={(resource) => `/resources/${resource.id}`}
      emptyMessage={emptyMessage ?? 'No resources available.'}
    />
  );
}
