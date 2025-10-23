/**
 * Podcast Player Repository
 *
 * Encapsulates AsyncStorage persistence for podcast player state.
 */

import type { InfrastructureProvider } from '../infrastructure/public';
import { infrastructureProvider } from '../infrastructure/public';
import type {
  GlobalPlayerState,
  PersistedUnitState,
  PlaybackSpeed,
} from './models';

export const GLOBAL_STATE_KEY = 'podcast_player:global_speed';
export const UNIT_STATE_PREFIX = 'podcast_player:unit:';

export class PodcastPlayerRepo {
  constructor(
    private infrastructure: InfrastructureProvider = infrastructureProvider()
  ) {}

  async getGlobalSpeed(): Promise<PlaybackSpeed | null> {
    const raw = await this.infrastructure.getStorageItem(GLOBAL_STATE_KEY);
    if (!raw) {
      return null;
    }

    try {
      const parsed = JSON.parse(raw) as Partial<GlobalPlayerState>;
      if (parsed && typeof parsed.speed === 'number') {
        return parsed.speed as PlaybackSpeed;
      }
    } catch (error) {
      console.warn('[PodcastPlayerRepo] Failed to parse global speed', error);
    }

    return null;
  }

  async saveGlobalSpeed(speed: PlaybackSpeed): Promise<void> {
    const payload: GlobalPlayerState = { speed };
    await this.infrastructure.setStorageItem(
      GLOBAL_STATE_KEY,
      JSON.stringify(payload)
    );
  }

  async getUnitPosition(unitId: string): Promise<number> {
    const state = await this.getUnitState(unitId);
    return state?.position ?? 0;
  }

  async saveUnitPosition(unitId: string, position: number): Promise<void> {
    const payload: PersistedUnitState = {
      position,
      updatedAt: Date.now(),
    };

    await this.infrastructure.setStorageItem(
      this.getUnitKey(unitId),
      JSON.stringify(payload)
    );
  }

  async getUnitState(unitId: string): Promise<PersistedUnitState | null> {
    const raw = await this.infrastructure.getStorageItem(
      this.getUnitKey(unitId)
    );
    if (!raw) {
      return null;
    }

    try {
      const parsed = JSON.parse(raw) as PersistedUnitState;
      if (
        parsed &&
        typeof parsed.position === 'number' &&
        Number.isFinite(parsed.position) &&
        typeof parsed.updatedAt === 'number'
      ) {
        return parsed;
      }
    } catch (error) {
      console.warn('[PodcastPlayerRepo] Failed to parse unit state', error);
    }

    return null;
  }

  private getUnitKey(unitId: string): string {
    return `${UNIT_STATE_PREFIX}${unitId}:position`;
  }
}
