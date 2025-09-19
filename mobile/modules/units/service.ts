/**
 * Units Module - Service
 *
 * Business logic for units; maps API → DTOs; returns DTOs only.
 */

import { UnitsRepo } from './repo';
import type { Unit, UnitDetail, UnitProgress } from './models';
import { toUnitDTO, toUnitDetailDTO } from './models';

export class UnitsService {
  constructor(private repo: UnitsRepo = new UnitsRepo()) {}

  async list(params?: { limit?: number; offset?: number }): Promise<Unit[]> {
    const apiUnits = await this.repo.list(params);
    return apiUnits.map(toUnitDTO);
  }

  async detail(unitId: string): Promise<UnitDetail | null> {
    if (!unitId?.trim()) return null;
    try {
      const api = await this.repo.detail(unitId);
      return toUnitDetailDTO(api);
    } catch (err: any) {
      if (err?.statusCode === 404) return null;
      throw err;
    }
  }

  async progress(unit: UnitDetail): Promise<UnitProgress> {
    const total = unit.lessons.length;
    // Naive progress: count lessons with any exercises as "completed" placeholder
    const completed = unit.lessons.filter(l => l.isReadyForLearning).length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    return {
      unitId: unit.id,
      completedLessons: completed,
      totalLessons: total,
      progressPercentage: pct,
    };
  }
}
