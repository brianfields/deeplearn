/**
 * Units Module - Public Interface
 *
 * Pure forwarder; exposes UnitsService methods for other modules.
 */

import { UnitsService } from './service';
import type { Unit, UnitDetail, UnitProgress } from './models';

export interface UnitsProvider {
  list(params?: { limit?: number; offset?: number }): Promise<Unit[]>;
  detail(unitId: string): Promise<UnitDetail | null>;
  progress(unit: UnitDetail): Promise<UnitProgress>;
}

let svc: UnitsService | null = null;
function getService(): UnitsService {
  if (!svc) svc = new UnitsService();
  return svc;
}

export function unitsProvider(): UnitsProvider {
  const service = getService();
  return {
    list: service.list.bind(service),
    detail: service.detail.bind(service),
    progress: service.progress.bind(service),
  };
}

export type { Unit, UnitDetail, UnitProgress } from './models';
