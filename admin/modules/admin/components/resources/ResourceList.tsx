import Link from 'next/link';
import type {
  ResourceSummary,
  ResourceUsageSummary,
} from '@/modules/admin/models';
import { formatDate } from '@/lib/utils';

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

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Resource
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Added
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Size
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Preview
            </th>
            {showUsageColumn && (
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Used In Units
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {resources.map((resource) => (
            <tr key={resource.id}>
              <td className="px-4 py-2 align-top text-sm text-gray-900">
                <div className="font-medium text-gray-900">{resourceLabel(resource)}</div>
                <div className="text-xs text-gray-500 capitalize">
                  {resource.resource_type.replace(/_/g, ' ')}
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
              </td>
              <td className="px-4 py-2 align-top text-sm text-gray-900">
                {formatDate(resource.created_at)}
              </td>
              <td className="px-4 py-2 align-top text-sm text-gray-900">
                {formatFileSize(resource.file_size ?? null)}
              </td>
              <td className="px-4 py-2 align-top text-sm text-gray-700">
                <div className="max-w-xs whitespace-pre-wrap break-words">
                  {normalizePreview(resource.preview_text)}
                </div>
              </td>
              {showUsageColumn && (
                <td className="px-4 py-2 align-top text-sm text-gray-900">
                  {resource.used_in_units && resource.used_in_units.length > 0 ? (
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
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
