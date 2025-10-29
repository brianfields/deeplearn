'use client';

import type { ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ReloadButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onClick'> {
  onReload: () => void | Promise<any>;
  isLoading?: boolean;
  label?: string;
}

export function ReloadButton({
  onReload,
  isLoading = false,
  label = 'Reload',
  className,
  disabled,
  ...rest
}: ReloadButtonProps) {
  return (
    <button
      type="button"
      onClick={onReload}
      disabled={disabled || isLoading}
      className={cn(
        'inline-flex items-center space-x-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-600 shadow-sm transition-colors hover:bg-gray-50 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-60',
        className
      )}
      {...rest}
    >
      <svg
        className={cn('h-4 w-4', isLoading && 'animate-spin')}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>
      <span>{isLoading ? 'Reloading…' : label}</span>
    </button>
  );
}
