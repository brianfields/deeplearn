declare module 'expo-sqlite' {
  export interface SQLResultSetRowList {
    length: number;
    item(index: number): any;
    _array: any[];
  }

  export interface SQLResultSet {
    insertId?: number | null;
    rows: SQLResultSetRowList;
    rowsAffected?: number;
  }

  export interface SQLTransaction {
    executeSql(
      sqlStatement: string,
      args?: any[],
      callback?: (transaction: SQLTransaction, resultSet: SQLResultSet) => void,
      errorCallback?: (
        transaction: SQLTransaction,
        error: any
      ) => boolean | void
    ): void;
  }

  export interface WebSQLDatabase {
    transaction(
      callback: (transaction: SQLTransaction) => void,
      errorCallback?: (error: any) => void,
      successCallback?: () => void
    ): void;
    readTransaction(
      callback: (transaction: SQLTransaction) => void,
      errorCallback?: (error: any) => void,
      successCallback?: () => void
    ): void;
    close(): void;
  }

  export function openDatabase(name: string): WebSQLDatabase;
}

declare module 'expo-file-system' {
  export interface FileInfo {
    exists: boolean;
    uri?: string;
    size?: number;
    modificationTime?: number;
    md5?: string | null;
  }

  export interface DownloadOptions {
    md5?: boolean;
    headers?: Record<string, string>;
  }

  export interface DownloadResult {
    uri: string;
    status: number;
    headers: Record<string, string>;
    md5?: string | null;
    bytesWritten?: number;
  }

  export function getInfoAsync(uri: string): Promise<FileInfo>;
  export function makeDirectoryAsync(
    uri: string,
    options?: { intermediates?: boolean }
  ): Promise<void>;
  export function deleteAsync(
    uri: string,
    options?: { idempotent?: boolean }
  ): Promise<void>;
  export function downloadAsync(
    uri: string,
    fileUri: string,
    options?: DownloadOptions
  ): Promise<DownloadResult>;
  export const documentDirectory: string | null;
}
