/**
 * Status Badge Component
 *
 * Displays status with appropriate colors and styling.
 */

import { cn, getStatusColor, capitalize } from '@/lib/utils';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function StatusBadge({ status, size = 'md', className }: StatusBadgeProps) {
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-1.5 text-sm',
    lg: 'px-3 py-2 text-base',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border',
        sizeClasses[size],
        getStatusColor(status),
        className
      )}
    >
      {capitalize(status)}
    </span>
  );
}
