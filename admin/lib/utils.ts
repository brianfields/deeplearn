export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
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
