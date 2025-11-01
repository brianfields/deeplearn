/**
 * Infrastructure Module - Service Layer
 *
 * Business logic and orchestration for infrastructure services.
 * Returns DTOs only, never raw API responses.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SQLiteImport from 'expo-sqlite';

// Use any for SQLite to avoid type conflicts with expo-sqlite v15+
const SQLite = SQLiteImport as any;
import * as FileSystem from 'expo-file-system';
import { InfrastructureRepo } from './repo';
import type {
  HttpClientConfig,
  RequestConfig,
  StorageConfig,
  StorageStats,
  NetworkStatus,
  InfrastructureHealth,
  SQLiteConfig,
  SQLiteMigration,
  SQLiteResultSet,
  FileInfo,
  FileDownloadResult,
  FileDownloadOptions,
} from './models';

export class InfrastructureService {
  private repo: InfrastructureRepo;
  private storageConfig: StorageConfig;
  private sqliteProviders: Map<string, SQLiteDatabaseProvider> = new Map();
  private fileSystemService: FileSystemService | null = null;

  constructor(httpConfig: HttpClientConfig, storageConfig: StorageConfig) {
    this.repo = new InfrastructureRepo(httpConfig);
    this.storageConfig = storageConfig;
  }

  // HTTP Client Methods (no caching - let React Query handle it)
  async request<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    return this.repo.request<T>(endpoint, config);
  }

  getNetworkStatus(): NetworkStatus {
    return this.repo.getNetworkStatus();
  }

  isOnline(): boolean {
    return this.repo.getNetworkStatus().isConnected !== false;
  }

  async checkHealth(): Promise<InfrastructureHealth> {
    const [httpHealth, storageHealth, networkStatus] = await Promise.allSettled(
      [
        this.repo.healthCheck(),
        this.checkStorageHealth(),
        Promise.resolve(this.repo.getNetworkStatus()),
      ]
    );

    return {
      httpClient: httpHealth.status === 'fulfilled' ? httpHealth.value : false,
      storage:
        storageHealth.status === 'fulfilled' ? storageHealth.value : false,
      network:
        networkStatus.status === 'fulfilled'
          ? networkStatus.value.isConnected
          : false,
      timestamp: Date.now(),
    };
  }

  // Simple storage utilities (for non-React Query data like user preferences)
  async getStorageItem(key: string): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(`${this.storageConfig.prefix}${key}`);
    } catch (error) {
      console.warn('[Storage] Read error:', error);
      return null;
    }
  }

  async setStorageItem(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(`${this.storageConfig.prefix}${key}`, value);
    } catch (error) {
      console.warn('[Storage] Write error:', error);
    }
  }

  async removeStorageItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(`${this.storageConfig.prefix}${key}`);
    } catch (error) {
      console.warn('[Storage] Remove error:', error);
    }
  }

  async getStorageStats(): Promise<StorageStats> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const storageKeys = keys.filter(key =>
        key.startsWith(this.storageConfig.prefix)
      );

      let totalSize = 0;
      for (const key of storageKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }

      return {
        entries: storageKeys.length,
        size: totalSize,
      };
    } catch {
      return { entries: 0, size: 0 };
    }
  }

  async clearStorage(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const storageKeys = keys.filter(key =>
        key.startsWith(this.storageConfig.prefix)
      );
      await AsyncStorage.multiRemove(storageKeys);
      console.log(`[Storage] Cleared ${storageKeys.length} entries`);
    } catch (error) {
      console.warn('[Storage] Clear error:', error);
    }
  }

  async createSQLiteProvider(
    config: SQLiteConfig
  ): Promise<SQLiteDatabaseProvider> {
    const existingProvider = this.sqliteProviders.get(config.databaseName);
    if (existingProvider) {
      await existingProvider.initialize();
      return existingProvider;
    }

    const provider = new SQLiteDatabaseProvider(config);
    await provider.initialize();
    this.sqliteProviders.set(config.databaseName, provider);
    return provider;
  }

  getFileSystem(): FileSystemService {
    if (!this.fileSystemService) {
      this.fileSystemService = new FileSystemService();
    }
    return this.fileSystemService;
  }

  private async checkStorageHealth(): Promise<boolean> {
    try {
      const testKey = `${this.storageConfig.prefix}health_check`;
      const testData = JSON.stringify({ test: true, timestamp: Date.now() });

      await AsyncStorage.setItem(testKey, testData);
      const retrieved = await AsyncStorage.getItem(testKey);
      await AsyncStorage.removeItem(testKey);

      return retrieved !== null;
    } catch {
      return false;
    }
  }
}

export interface SQLiteExecutor {
  execute(sql: string, params?: unknown[]): Promise<SQLiteResultSet>;
}

class SQLiteSyncExecutor implements SQLiteExecutor {
  private database: any;

  constructor(database: any) {
    this.database = database;
  }

  async execute(sql: string, params: unknown[] = []): Promise<SQLiteResultSet> {
    try {
      // Use runSync for INSERT/UPDATE/DELETE, getAllSync for SELECT
      const normalizedSql = sql.trim().toUpperCase();

      if (normalizedSql.startsWith('SELECT')) {
        const result = this.database.getAllSync(sql, params);
        return {
          rows: result,
          rowsAffected: 0,
          insertId: null,
        };
      } else if (normalizedSql.startsWith('PRAGMA')) {
        // PRAGMA statements don't return rows in expo-sqlite v15
        this.database.execSync(sql);
        return {
          rows: [],
          rowsAffected: 0,
          insertId: null,
        };
      } else {
        // INSERT, UPDATE, DELETE, CREATE TABLE, etc.
        const result = this.database.runSync(sql, params);
        return {
          rows: [],
          rowsAffected: result.changes ?? 0,
          insertId: result.lastInsertRowId ?? null,
        };
      }
    } catch (error) {
      console.error('[SQLite] Execute error:', error, 'SQL:', sql);
      throw error;
    }
  }
}

export class SQLiteDatabaseProvider {
  private config: SQLiteConfig;
  private database: any | null = null;
  private initialized = false;

  constructor(config: SQLiteConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    if (!this.database) {
      this.database = SQLite.openDatabaseSync(this.config.databaseName);
    }

    if (this.config.enableForeignKeys) {
      await this.transaction(async executor => {
        await executor.execute('PRAGMA foreign_keys = ON;');
      });
    }

    await this.runMigrations();
    this.initialized = true;
  }

  async execute(sql: string, params: unknown[] = []): Promise<SQLiteResultSet> {
    const db = this.ensureDatabase();
    const executor = new SQLiteSyncExecutor(db);
    return executor.execute(sql, params);
  }

  async transaction<T>(
    fn: (executor: SQLiteExecutor) => Promise<T>
  ): Promise<T> {
    const db = this.ensureDatabase();
    const executor = new SQLiteSyncExecutor(db);
    return fn(executor);
  }

  async close(): Promise<void> {
    if (this.database && typeof this.database.closeSync === 'function') {
      try {
        this.database.closeSync();
      } catch (error) {
        console.warn('[SQLite] Close error:', error);
      }
    }
    this.database = null;
    this.initialized = false;
  }

  private async runMigrations(): Promise<void> {
    const migrations: SQLiteMigration[] = [...this.config.migrations].sort(
      (a, b) => a.id - b.id
    );

    if (migrations.length === 0) {
      return;
    }

    await this.transaction(async executor => {
      // Create migrations tracking table
      await executor.execute(`
        CREATE TABLE IF NOT EXISTS _migrations (
          id INTEGER PRIMARY KEY,
          applied_at INTEGER NOT NULL
        );
      `);

      // Get already applied migrations
      const appliedResult = await executor.execute(
        'SELECT id FROM _migrations ORDER BY id;'
      );
      const appliedIds = new Set(appliedResult.rows.map((row: any) => row.id));

      // Run pending migrations
      for (const migration of migrations) {
        if (appliedIds.has(migration.id)) {
          continue; // Skip already applied migration
        }

        for (const statement of migration.statements) {
          await executor.execute(statement);
        }

        // Record migration as applied
        await executor.execute(
          'INSERT INTO _migrations (id, applied_at) VALUES (?, ?);',
          [migration.id, Date.now()]
        );
      }
    });
  }

  private ensureDatabase(): any {
    if (!this.database) {
      this.database = SQLite.openDatabaseSync(this.config.databaseName);
    }
    return this.database;
  }

  async getDatabaseInfo(): Promise<{ path: string; name: string }> {
    const dbName = this.config.databaseName;
    // expo-sqlite stores databases in SQLite directory by default
    const dbPath = `${FileSystem.documentDirectory}SQLite/${dbName}`;
    return {
      name: dbName,
      path: dbPath,
    };
  }
}

export class FileSystemService {
  async getInfo(uri: string): Promise<FileInfo> {
    try {
      const info = await FileSystem.getInfoAsync(uri);
      if (!info.exists) {
        return { exists: false, uri: info.uri };
      }
      return {
        exists: info.exists,
        uri: info.uri,
        size: info.size,
        modificationTime: info.modificationTime ?? undefined,
      };
    } catch (error) {
      console.warn('[FileSystem] getInfo error:', error);
      return { exists: false };
    }
  }

  async ensureDirectory(directoryUri: string): Promise<void> {
    if (!directoryUri) {
      return;
    }

    try {
      const info = await FileSystem.getInfoAsync(directoryUri);
      if (!info.exists) {
        await FileSystem.makeDirectoryAsync(directoryUri, {
          intermediates: true,
        });
      }
    } catch (error) {
      console.warn('[FileSystem] ensureDirectory error:', error);
      throw error;
    }
  }

  async downloadFile(
    remoteUri: string,
    localUri: string,
    options: FileDownloadOptions = {}
  ): Promise<FileDownloadResult> {
    if (options.skipIfExists) {
      const existing = await this.getInfo(localUri);
      if (existing.exists) {
        return {
          uri: localUri,
          status: 'completed',
          bytesWritten: existing.size ?? 0,
        };
      }
    }

    const directory = extractDirectory(localUri);
    await this.ensureDirectory(directory);

    const result = await FileSystem.downloadAsync(remoteUri, localUri);
    return {
      uri: result.uri,
      status: result.status === 200 ? 'completed' : 'failed',
      bytesWritten: (result as any).bytesWritten,
    };
  }

  async deleteFile(localUri: string): Promise<void> {
    try {
      await FileSystem.deleteAsync(localUri, { idempotent: true });
    } catch (error) {
      console.warn('[FileSystem] deleteFile error:', error);
    }
  }
}

export const OLDEST_SUPPORTED_UNIT_SCHEMA = 1;

function extractDirectory(fileUri: string): string {
  const normalized = fileUri.replace(/\\/g, '/');
  const lastSlash = normalized.lastIndexOf('/');
  if (lastSlash === -1) {
    return normalized;
  }
  return normalized.slice(0, lastSlash);
}
