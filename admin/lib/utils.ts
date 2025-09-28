const STATUS_VARIANTS: Record<string, string> = {
  success: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  info: 'bg-sky-100 text-sky-800 border-sky-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  error: 'bg-rose-100 text-rose-800 border-rose-200',
  secondary: 'bg-slate-100 text-slate-600 border-slate-200',
};

const STATUS_COLORS: Record<string, string> = {
  pending: STATUS_VARIANTS.warning,
  running: STATUS_VARIANTS.info,
  completed: STATUS_VARIANTS.success,
  success: STATUS_VARIANTS.success,
  failed: STATUS_VARIANTS.error,
  error: STATUS_VARIANTS.error,
  cancelled: STATUS_VARIANTS.secondary,
  paused: STATUS_VARIANTS.secondary,
  healthy: STATUS_VARIANTS.success,
  degraded: STATUS_VARIANTS.warning,
  down: STATUS_VARIANTS.error,
  offline: STATUS_VARIANTS.secondary,
  busy: STATUS_VARIANTS.info,
};

export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

export function capitalize(value: string | null | undefined): string {
  if (!value) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function getStatusColor(status: string | null | undefined): string {
  const normalized = (status ?? '').toLowerCase();
  return STATUS_COLORS[normalized] ?? STATUS_VARIANTS.secondary;
}

export function getVariantColor(variant: string | null | undefined): string {
  if (!variant) return STATUS_VARIANTS.secondary;
  return STATUS_VARIANTS[variant] ?? variant;
}

export function formatPercentage(
  value: number | null | undefined,
  fractionDigits = 1
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  const formatted = Number(value).toFixed(fractionDigits);
  return `${formatted}%`;
}

export function formatJSON(value: unknown): string {
  if (value === null || value === undefined) {
    return '—';
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    return String(value);
  }
}

export function formatDate(value: Date | string | null | undefined): string {
  if (!value) return '—';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString();
}

export function formatExecutionTime(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—';
  }
  if (value < 1000) {
    return `${Math.round(value)} ms`;
  }
  const seconds = value / 1000;
  if (seconds < 60) {
    return `${seconds.toFixed(1)} s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds.toFixed(0)}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

export function formatTokens(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—';
  }
  if (value < 1000) {
    return `${value}`;
  }
  if (value < 1000000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return `${(value / 1000000).toFixed(1)}M`;
}

export function formatCost(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—';
  }
  return `$${value.toFixed(4)}`;
}
