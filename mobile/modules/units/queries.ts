/**
 * Units Module - React Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import { unitsProvider } from './public';
import type { UnitDetail } from './models';

const svc = unitsProvider();

export const qk = {
  all: ['units'] as const,
  list: (p?: { limit?: number; offset?: number }) =>
    ['units', 'list', p ?? {}] as const,
  detail: (id: string) => ['units', 'detail', id] as const,
  progress: (id: string) => ['units', 'progress', id] as const,
};

export function useUnits(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: qk.list(params),
    queryFn: () => svc.list(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUnit(unitId: string) {
  return useQuery({
    queryKey: qk.detail(unitId),
    queryFn: () => svc.detail(unitId),
    enabled: !!unitId?.trim(),
    staleTime: 10 * 60 * 1000,
  });
}

export function useUnitProgress(unit: UnitDetail | null | undefined) {
  return useQuery({
    queryKey: qk.progress(unit?.id || ''),
    queryFn: () => svc.progress(unit as UnitDetail),
    enabled: !!unit,
    staleTime: 60 * 1000,
  });
}
