'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useResource } from '@/modules/admin/queries';
import { LoadingSpinner } from '@/modules/admin/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/modules/admin/components/shared/ErrorMessage';
import { ResourceTypeBadge } from '@/modules/admin/components/resources/ResourceList';
import { formatDate } from '@/lib/utils';

interface ResourceDetailPageProps {
  params: { id: string };
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

const formatMetadataKey = (key: string): string => {
  return key
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
};

export default function ResourceDetailPage({ params }: ResourceDetailPageProps): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();
  const downloadParam = searchParams?.get('download');
  const shouldAutoDownload = downloadParam === '1' || downloadParam === 'true';
  const [hasDownloaded, setHasDownloaded] = useState(false);
  const {
    data: resource,
    isLoading,
    isError,
    refetch,
  } = useResource(params.id);

  const downloadResource = useCallback(() => {
    if (!resource) {
      return;
    }
    const baseName = (resource.filename ?? resource.resource_type ?? 'resource')
      .replace(/\.[^/.]+$/, '')
      .replace(/[^a-zA-Z0-9-_]+/g, '-');
    const downloadName = `${baseName || 'resource'}-${resource.id}.txt`;
    const blob = new Blob([resource.extracted_text ?? ''], {
      type: 'text/plain;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = downloadName;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }, [resource]);

  useEffect(() => {
    if (resource && shouldAutoDownload && !hasDownloaded) {
      downloadResource();
      setHasDownloaded(true);
    }
  }, [resource, shouldAutoDownload, hasDownloaded, downloadResource]);

  const metadataEntries = useMemo(() => {
    if (!resource?.extraction_metadata) {
      return [] as Array<[string, unknown]>;
    }
    return Object.entries(resource.extraction_metadata).filter(([, value]) => {
      if (value === null || value === undefined) {
        return false;
      }
      if (typeof value === 'string') {
        return value.trim().length > 0;
      }
      return true;
    });
  }, [resource]);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading resource..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="Failed to load resource."
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  if (!resource) {
    return (
      <div className="space-y-4 text-center">
        <p className="text-gray-600">We couldn&apos;t find a resource with that identifier.</p>
        <div className="flex justify-center gap-4">
          <Link href="/units" className="text-blue-600 hover:text-blue-500">
            ← Back to units
          </Link>
          <Link href="/users" className="text-blue-600 hover:text-blue-500">
            Browse users
          </Link>
        </div>
      </div>
    );
  }

  const onDownloadClick = () => {
    downloadResource();
    setHasDownloaded(true);
  };

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => router.back()}
        className="text-sm text-gray-500 hover:text-gray-700"
      >
        ← Back
      </button>

      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {resource.filename || formatMetadataKey(resource.resource_type) || resource.id}
            </h1>
            <p className="mt-1 text-sm text-gray-500">Resource ID: {resource.id}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <ResourceTypeBadge resourceType={resource.resource_type} />
              <span className="text-sm text-gray-500">User ID: {resource.user_id}</span>
              <span className="text-sm text-gray-500">
                Created {formatDate(resource.created_at)}
              </span>
              <span className="text-sm text-gray-500">
                Updated {formatDate(resource.updated_at)}
              </span>
            </div>
          </div>
          <div className="flex flex-col items-start md:items-end gap-2">
            <button
              type="button"
              onClick={onDownloadClick}
              className="inline-flex items-center rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-violet-700"
            >
              Download text
            </button>
            {resource.source_url && (
              <a
                href={resource.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:text-blue-500 text-sm"
              >
                Open original source →
              </a>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              File information
            </h2>
            <dl className="space-y-1 text-sm text-gray-700">
              <div className="flex justify-between">
                <dt className="text-gray-500">File size</dt>
                <dd>{formatFileSize(resource.file_size ?? null)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Source URL</dt>
                <dd className="text-right text-blue-600">
                  {resource.source_url ? (
                    <a href={resource.source_url} target="_blank" rel="noreferrer">
                      {resource.source_url}
                    </a>
                  ) : (
                    '—'
                  )}
                </dd>
              </div>
            </dl>
          </div>
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Extraction metadata
            </h2>
            {metadataEntries.length > 0 ? (
              <dl className="space-y-1 text-sm text-gray-700">
                {metadataEntries.map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3">
                    <dt className="text-gray-500">{formatMetadataKey(key)}</dt>
                    <dd className="text-right break-words">
                      {typeof value === 'string' ? value : JSON.stringify(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-sm text-gray-500">No metadata recorded for this resource.</p>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
            Extracted text
          </h2>
          <div className="max-h-[32rem] overflow-y-auto rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-800 whitespace-pre-wrap">
            {resource.extracted_text?.trim() ? resource.extracted_text : 'No extracted text available.'}
          </div>
        </div>
      </div>
    </div>
  );
}
