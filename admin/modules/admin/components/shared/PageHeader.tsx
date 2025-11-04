'use client';

import { ReactNode } from 'react';
import { ReloadButton } from './ReloadButton';

interface PageHeaderProps {
  title: string;
  description?: string;
  onReload?: () => void | Promise<any>;
  isReloading?: boolean;
  action?: ReactNode;
}

export function PageHeader({
  title,
  description,
  onReload,
  isReloading = false,
  action,
}: PageHeaderProps): JSX.Element {
  return (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        {description && (
          <p className="mt-2 text-gray-600">{description}</p>
        )}
      </div>

      <div className="flex items-center gap-3 ml-6">
        {onReload && (
          <ReloadButton
            onReload={onReload}
            isLoading={isReloading}
            label="Reload"
          />
        )}
        {action}
      </div>
    </div>
  );
}
