/**
 * Offline Cache Module - Repository Layer
 *
 * Encapsulates SQLite access for cached units, lessons, assets, outbox, and metadata.
 */

import type {
  SQLiteDatabaseProvider,
  SQLiteMigration,
} from '../infrastructure/public';
import type {
  CachedUnit,
  CachedLesson,
  CachedAsset,
  CachedUnitDetail,
  OutboxRecord,
  OutboxRequest,
} from './models';

export const OFFLINE_CACHE_MIGRATIONS: SQLiteMigration[] = [
  {
    id: 1,
    statements: [
      `CREATE TABLE IF NOT EXISTS units (
        id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        learner_level TEXT,
        is_global INTEGER,
        updated_at INTEGER,
        schema_version INTEGER,
        download_status TEXT,
        cache_mode TEXT,
        downloaded_at INTEGER,
        synced_at INTEGER
      );`,
      `CREATE TABLE IF NOT EXISTS lessons (
        id TEXT PRIMARY KEY,
        unit_id TEXT,
        title TEXT,
        position INTEGER,
        payload TEXT,
        updated_at INTEGER,
        schema_version INTEGER
      );`,
      `CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY,
        unit_id TEXT,
        type TEXT,
        remote_uri TEXT,
        checksum TEXT,
        updated_at INTEGER,
        local_path TEXT,
        status TEXT,
        downloaded_at INTEGER
      );`,
      `CREATE TABLE IF NOT EXISTS outbox (
        id TEXT PRIMARY KEY,
        endpoint TEXT,
        method TEXT,
        payload TEXT,
        headers TEXT,
        idempotency_key TEXT,
        attempts INTEGER,
        last_error TEXT,
        next_attempt_at INTEGER,
        created_at INTEGER,
        updated_at INTEGER
      );`,
      `CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at INTEGER
      );`,
    ],
  },
  {
    id: 2,
    statements: [`ALTER TABLE units ADD COLUMN unit_payload TEXT;`],
  },
];

export class OfflineCacheRepository {
  private provider: SQLiteDatabaseProvider;

  constructor(provider: SQLiteDatabaseProvider) {
    this.provider = provider;
  }

  async initialize(): Promise<void> {
    await this.provider.initialize();
  }

  async upsertUnits(units: CachedUnit[]): Promise<void> {
    if (units.length === 0) {
      return;
    }

    await this.provider.transaction(async executor => {
      for (const unit of units) {
        await executor.execute(
          `INSERT OR REPLACE INTO units (
            id, title, description, learner_level, is_global, updated_at,
            schema_version, download_status, cache_mode, downloaded_at, synced_at, unit_payload
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);`,
          [
            unit.id,
            unit.title,
            unit.description,
            unit.learnerLevel,
            unit.isGlobal ? 1 : 0,
            unit.updatedAt,
            unit.schemaVersion,
            unit.downloadStatus,
            unit.cacheMode,
            unit.downloadedAt ?? null,
            unit.syncedAt ?? null,
            unit.unitPayload ? JSON.stringify(unit.unitPayload) : null,
          ]
        );
      }
    });
  }

  async getUnit(unitId: string): Promise<CachedUnit | null> {
    const result = await this.provider.execute(
      `SELECT * FROM units WHERE id = ? LIMIT 1;`,
      [unitId]
    );
    if (result.rows.length === 0) {
      return null;
    }
    return mapUnitRow(result.rows[0]);
  }

  async listUnits(): Promise<CachedUnit[]> {
    const result = await this.provider.execute(
      `SELECT * FROM units ORDER BY updated_at DESC;`
    );
    return result.rows.map(mapUnitRow);
  }

  async deleteUnit(unitId: string): Promise<void> {
    await this.provider.transaction(async executor => {
      await executor.execute(`DELETE FROM lessons WHERE unit_id = ?;`, [
        unitId,
      ]);
      await executor.execute(`DELETE FROM assets WHERE unit_id = ?;`, [unitId]);
      await executor.execute(`DELETE FROM units WHERE id = ?;`, [unitId]);
    });
  }

  async deleteUnitsBelowSchemaVersion(schemaVersion: number): Promise<void> {
    await this.provider.execute(`DELETE FROM units WHERE schema_version < ?;`, [
      schemaVersion,
    ]);
  }

  async clearMinimalUnits(): Promise<void> {
    await this.provider.transaction(async executor => {
      // Delete lessons and assets for minimal units only
      await executor.execute(
        `DELETE FROM lessons WHERE unit_id IN (SELECT id FROM units WHERE cache_mode = 'minimal');`
      );
      await executor.execute(
        `DELETE FROM assets WHERE unit_id IN (SELECT id FROM units WHERE cache_mode = 'minimal');`
      );
      // Delete minimal units
      await executor.execute(`DELETE FROM units WHERE cache_mode = 'minimal';`);
    });
  }

  async replaceLessons(unitId: string, lessons: CachedLesson[]): Promise<void> {
    await this.provider.transaction(async executor => {
      await executor.execute(`DELETE FROM lessons WHERE unit_id = ?;`, [
        unitId,
      ]);
      for (const lesson of lessons) {
        await executor.execute(
          `INSERT OR REPLACE INTO lessons (
            id, unit_id, title, position, payload, updated_at, schema_version
          ) VALUES (?, ?, ?, ?, ?, ?, ?);`,
          [
            lesson.id,
            lesson.unitId,
            lesson.title,
            lesson.position,
            JSON.stringify(lesson.payload ?? null),
            lesson.updatedAt,
            lesson.schemaVersion,
          ]
        );
      }
    });
  }

  async upsertLessons(lessons: CachedLesson[]): Promise<void> {
    if (lessons.length === 0) {
      return;
    }

    await this.provider.transaction(async executor => {
      for (const lesson of lessons) {
        await executor.execute(
          `INSERT OR REPLACE INTO lessons (
            id, unit_id, title, position, payload, updated_at, schema_version
          ) VALUES (?, ?, ?, ?, ?, ?, ?);`,
          [
            lesson.id,
            lesson.unitId,
            lesson.title,
            lesson.position,
            JSON.stringify(lesson.payload ?? null),
            lesson.updatedAt,
            lesson.schemaVersion,
          ]
        );
      }
    });
  }

  async getLessons(unitId: string): Promise<CachedLesson[]> {
    const result = await this.provider.execute(
      `SELECT * FROM lessons WHERE unit_id = ? ORDER BY position ASC;`,
      [unitId]
    );
    return result.rows.map(mapLessonRow);
  }

  async replaceAssets(unitId: string, assets: CachedAsset[]): Promise<void> {
    await this.provider.transaction(async executor => {
      await executor.execute(`DELETE FROM assets WHERE unit_id = ?;`, [unitId]);
      for (const asset of assets) {
        await executor.execute(
          `INSERT OR REPLACE INTO assets (
            id, unit_id, type, remote_uri, checksum, updated_at,
            local_path, status, downloaded_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);`,
          [
            asset.id,
            asset.unitId,
            asset.type,
            asset.remoteUri,
            asset.checksum ?? null,
            asset.updatedAt,
            asset.localPath ?? null,
            asset.status,
            asset.downloadedAt ?? null,
          ]
        );
      }
    });
  }

  async upsertAssets(assets: CachedAsset[]): Promise<void> {
    if (assets.length === 0) {
      return;
    }

    await this.provider.transaction(async executor => {
      for (const asset of assets) {
        await executor.execute(
          `INSERT OR REPLACE INTO assets (
            id, unit_id, type, remote_uri, checksum, updated_at,
            local_path, status, downloaded_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);`,
          [
            asset.id,
            asset.unitId,
            asset.type,
            asset.remoteUri,
            asset.checksum ?? null,
            asset.updatedAt,
            asset.localPath ?? null,
            asset.status,
            asset.downloadedAt ?? null,
          ]
        );
      }
    });
  }

  async getAssets(unitId: string): Promise<CachedAsset[]> {
    const result = await this.provider.execute(
      `SELECT * FROM assets WHERE unit_id = ? ORDER BY id ASC;`,
      [unitId]
    );
    return result.rows.map(mapAssetRow);
  }

  async getAssetById(assetId: string): Promise<CachedAsset | null> {
    const result = await this.provider.execute(
      `SELECT * FROM assets WHERE id = ? LIMIT 1;`,
      [assetId]
    );
    if (result.rows.length === 0) {
      return null;
    }
    return mapAssetRow(result.rows[0]);
  }

  async updateAssetLocation(
    assetId: string,
    localPath: string,
    status: string,
    downloadedAt: number
  ): Promise<void> {
    await this.provider.execute(
      `UPDATE assets SET local_path = ?, status = ?, downloaded_at = ? WHERE id = ?;`,
      [localPath, status, downloadedAt, assetId]
    );
  }

  async removeAssets(unitId: string): Promise<void> {
    await this.provider.execute(`DELETE FROM assets WHERE unit_id = ?;`, [
      unitId,
    ]);
  }

  async listAllAssets(): Promise<CachedAsset[]> {
    const result = await this.provider.execute(`SELECT * FROM assets;`);
    return result.rows.map(mapAssetRow);
  }

  async clearAll(): Promise<void> {
    await this.provider.transaction(async executor => {
      await executor.execute('DELETE FROM lessons;');
      await executor.execute('DELETE FROM assets;');
      await executor.execute('DELETE FROM outbox;');
      await executor.execute('DELETE FROM metadata;');
      await executor.execute('DELETE FROM units;');
    });

    // VACUUM to reclaim space and shrink the database file
    await this.provider.execute('VACUUM;');
  }

  async enqueueOutbox(
    request: OutboxRequest & { id: string },
    timestamp: number
  ): Promise<void> {
    await this.provider.execute(
      `INSERT INTO outbox (
        id, endpoint, method, payload, headers, idempotency_key,
        attempts, last_error, next_attempt_at, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);`,
      [
        request.id,
        request.endpoint,
        request.method,
        JSON.stringify(request.payload ?? null),
        request.headers ? JSON.stringify(request.headers) : null,
        request.idempotencyKey,
        0,
        null,
        timestamp,
        timestamp,
        timestamp,
      ]
    );
  }

  async listOutbox(): Promise<OutboxRecord[]> {
    const result = await this.provider.execute(
      `SELECT * FROM outbox ORDER BY created_at ASC;`
    );
    return result.rows.map(mapOutboxRow);
  }

  async updateOutboxFailure(
    id: string,
    attempts: number,
    error: string,
    nextAttemptAt: number,
    timestamp: number
  ): Promise<void> {
    await this.provider.execute(
      `UPDATE outbox SET attempts = ?, last_error = ?, next_attempt_at = ?, updated_at = ? WHERE id = ?;`,
      [attempts, error, nextAttemptAt, timestamp, id]
    );
  }

  async deleteOutbox(id: string): Promise<void> {
    await this.provider.execute(`DELETE FROM outbox WHERE id = ?;`, [id]);
  }

  async countOutbox(): Promise<number> {
    const result = await this.provider.execute(
      `SELECT COUNT(*) as count FROM outbox;`
    );
    if (result.rows.length === 0) {
      return 0;
    }
    const row = result.rows[0] as { count?: number };
    return (row.count as number) ?? 0;
  }

  async setMetadata(key: string, value: string): Promise<void> {
    const timestamp = Date.now();
    await this.provider.execute(
      `INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?);`,
      [key, value, timestamp]
    );
  }

  async getMetadata(key: string): Promise<string | null> {
    const result = await this.provider.execute(
      `SELECT value FROM metadata WHERE key = ?;`,
      [key]
    );
    if (result.rows.length === 0) {
      return null;
    }
    const row = result.rows[0] as { value?: string | null };
    return (row.value as string) ?? null;
  }

  async buildUnitDetail(unitId: string): Promise<CachedUnitDetail | null> {
    const unit = await this.getUnit(unitId);
    if (!unit) {
      return null;
    }
    const [lessons, assets] = await Promise.all([
      this.getLessons(unitId),
      this.getAssets(unitId),
    ]);
    return {
      ...unit,
      lessons,
      assets,
    };
  }
}

function mapUnitRow(row: any): CachedUnit {
  let unitPayload: CachedUnit['unitPayload'] = null;
  if (row.unit_payload) {
    try {
      unitPayload = JSON.parse(row.unit_payload);
    } catch {
      unitPayload = null;
    }
  }
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    learnerLevel: row.learner_level,
    isGlobal: Boolean(row.is_global),
    updatedAt: Number(row.updated_at),
    schemaVersion: Number(row.schema_version),
    downloadStatus: row.download_status,
    cacheMode: row.cache_mode,
    downloadedAt: row.downloaded_at ?? null,
    syncedAt: row.synced_at ?? null,
    unitPayload,
  };
}

function mapLessonRow(row: any): CachedLesson {
  let payload: unknown = null;
  if (row.payload) {
    try {
      payload = JSON.parse(row.payload);
    } catch {
      payload = row.payload;
    }
  }
  return {
    id: row.id,
    unitId: row.unit_id,
    title: row.title,
    position: Number(row.position),
    payload,
    updatedAt: Number(row.updated_at),
    schemaVersion: Number(row.schema_version),
  };
}

function mapAssetRow(row: any): CachedAsset {
  return {
    id: row.id,
    unitId: row.unit_id,
    type: row.type,
    remoteUri: row.remote_uri,
    checksum: row.checksum ?? null,
    updatedAt: Number(row.updated_at),
    localPath: row.local_path ?? null,
    status: row.status,
    downloadedAt: row.downloaded_at ?? null,
  };
}

function mapOutboxRow(row: any): OutboxRecord {
  let payload: unknown = null;
  if (row.payload) {
    try {
      payload = JSON.parse(row.payload);
    } catch {
      payload = row.payload;
    }
  }
  let headers: Record<string, string> | undefined;
  if (row.headers) {
    try {
      headers = JSON.parse(row.headers);
    } catch {
      headers = undefined;
    }
  }
  return {
    id: row.id,
    endpoint: row.endpoint,
    method: row.method,
    payload,
    headers,
    idempotencyKey: row.idempotency_key,
    attempts: Number(row.attempts ?? 0),
    lastError: row.last_error ?? null,
    nextAttemptAt: Number(row.next_attempt_at ?? 0),
    createdAt: Number(row.created_at ?? 0),
    updatedAt: Number(row.updated_at ?? 0),
  };
}
