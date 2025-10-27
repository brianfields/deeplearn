/**
 * SQLiteDetailScreen - Detailed SQLite Database Information
 *
 * Shows complete database contents including tables and data.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import * as FileSystem from 'expo-file-system';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import {
  Box,
  Card,
  Text,
  Button,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { infrastructureProvider } from '../../infrastructure/public';
import type { LearningStackParamList } from '../../../types';
import { OFFLINE_CACHE_MIGRATIONS } from '../repo';

type SQLiteDetailNavigation = NativeStackNavigationProp<
  LearningStackParamList,
  'SQLiteDetail'
>;

interface TableInfo {
  name: string;
  rowCount: number;
  sampleRows: Array<Record<string, any>>;
}

interface SQLiteInfo {
  dbSize: number;
  dbPath: string | null;
  dbName: string;
  exists: boolean;
  tables: TableInfo[];
  loading: boolean;
}

export function SQLiteDetailScreen(): React.ReactElement {
  const navigation = useNavigation<SQLiteDetailNavigation>();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const [sqliteInfo, setSqliteInfo] = useState<SQLiteInfo>({
    dbSize: 0,
    dbPath: null,
    dbName: 'offline_unit_cache.db',
    exists: false,
    tables: [],
    loading: true,
  });
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());

  const loadSQLiteInfo = useCallback(async () => {
    setSqliteInfo(prev => ({ ...prev, loading: true }));

    try {
      const infra = infrastructureProvider();
      const sqliteProvider = await infra.createSQLiteProvider({
        databaseName: 'offline_unit_cache.db',
        enableForeignKeys: true,
        migrations: OFFLINE_CACHE_MIGRATIONS,
      });

      await sqliteProvider.initialize();

      let dbSize = 0;
      let dbPath: string | null = null;
      let exists = false;

      try {
        const dbInfo = await sqliteProvider.getDatabaseInfo();
        dbPath = dbInfo.path;
        if (dbPath) {
          const fileInfo = await FileSystem.getInfoAsync(dbPath);
          if (fileInfo.exists) {
            dbSize = fileInfo.size || 0;
            exists = true;
          }
        }
      } catch (error) {
        console.warn('[SQLiteDetail] Failed to get SQLite info:', error);
      }

      // Get list of tables
      const tables: TableInfo[] = [];
      try {
        const tablesResult = await sqliteProvider.execute(
          "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        );

        for (const row of tablesResult.rows) {
          const tableName = row.name as string;

          // Get row count
          let rowCount = 0;
          try {
            const countResult = await sqliteProvider.execute(
              `SELECT COUNT(*) as count FROM ${tableName}`
            );
            rowCount = (countResult.rows[0]?.count as number) || 0;
          } catch (error) {
            console.warn(
              `[SQLiteDetail] Failed to count rows in ${tableName}:`,
              error
            );
          }

          // Get sample rows (first 5)
          const sampleRows: Array<Record<string, any>> = [];
          try {
            const dataResult = await sqliteProvider.execute(
              `SELECT * FROM ${tableName} LIMIT 5`
            );
            sampleRows.push(...dataResult.rows);
          } catch (error) {
            console.warn(`[SQLiteDetail] Failed to query ${tableName}:`, error);
          }

          tables.push({
            name: tableName,
            rowCount,
            sampleRows,
          });
        }
      } catch (error) {
        console.warn('[SQLiteDetail] Failed to get tables:', error);
      }

      setSqliteInfo({
        dbSize,
        dbPath,
        dbName: 'offline_unit_cache.db',
        exists,
        tables,
        loading: false,
      });
    } catch (error) {
      console.error('[SQLiteDetail] Failed to load SQLite info:', error);
      setSqliteInfo(prev => ({ ...prev, loading: false }));
    }
  }, []);

  useEffect(() => {
    loadSQLiteInfo();
  }, [loadSQLiteInfo]);

  const toggleTable = useCallback((tableName: string) => {
    setExpandedTables(prev => {
      const next = new Set(prev);
      if (next.has(tableName)) {
        next.delete(tableName);
      } else {
        next.add(tableName);
      }
      return next;
    });
  }, []);

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Box p="lg" pb="sm">
          <TouchableOpacity
            onPress={() => {
              haptics.trigger('light');
              navigation.goBack();
            }}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            style={styles.backButton}
          >
            <Text variant="body" color={theme.colors.primary}>
              {'‹ Back'}
            </Text>
          </TouchableOpacity>
          <Text variant="h1" style={styles.title}>
            SQLite Database
          </Text>
          <Text variant="secondary" color={theme.colors.textSecondary}>
            Complete database contents
          </Text>
        </Box>

        {sqliteInfo.loading ? (
          <Box p="lg">
            <ActivityIndicator size="large" color={theme.colors.primary} />
          </Box>
        ) : (
          <>
            {/* Database Summary */}
            <Box px="lg" mb="md">
              <Card variant="default">
                <View style={styles.statRow}>
                  <View style={styles.statItem}>
                    <Text
                      variant="secondary"
                      color={theme.colors.textSecondary}
                    >
                      Size
                    </Text>
                    <Text variant="h2" color={theme.colors.primary}>
                      {formatBytes(sqliteInfo.dbSize)}
                    </Text>
                  </View>
                  <View style={styles.statItem}>
                    <Text
                      variant="secondary"
                      color={theme.colors.textSecondary}
                    >
                      Tables
                    </Text>
                    <Text variant="h2" color={theme.colors.primary}>
                      {sqliteInfo.tables.length}
                    </Text>
                  </View>
                </View>
              </Card>
            </Box>

            {sqliteInfo.dbPath && (
              <Box px="lg" mb="md">
                <Card variant="outlined">
                  <Text variant="caption" color={theme.colors.textSecondary}>
                    Database Path:
                  </Text>
                  <Text
                    variant="caption"
                    color={theme.colors.text}
                    style={styles.pathText}
                    selectable
                  >
                    {sqliteInfo.dbPath}
                  </Text>
                </Card>
              </Box>
            )}

            <Box px="lg" mb="md">
              <Button
                title="Refresh"
                variant="secondary"
                size="medium"
                fullWidth
                onPress={() => {
                  haptics.trigger('light');
                  loadSQLiteInfo();
                }}
                testID="refresh-sqlite-info"
              />
            </Box>

            {/* Tables */}
            {sqliteInfo.tables.length === 0 ? (
              <Box px="lg">
                <Card variant="outlined">
                  <Text variant="body" color={theme.colors.textSecondary}>
                    No tables in database
                  </Text>
                </Card>
              </Box>
            ) : (
              <Box px="lg">
                <Text variant="title" style={{ marginBottom: 12 }}>
                  Tables & Data
                </Text>
                {sqliteInfo.tables.map(table => {
                  const isExpanded = expandedTables.has(table.name);
                  return (
                    <Card
                      key={table.name}
                      variant="outlined"
                      style={{ marginBottom: 12 }}
                    >
                      <TouchableOpacity
                        onPress={() => {
                          haptics.trigger('light');
                          toggleTable(table.name);
                        }}
                        activeOpacity={0.7}
                      >
                        <View style={styles.tableHeader}>
                          <Text
                            variant="body"
                            style={{ fontWeight: '600', flex: 1 }}
                          >
                            {table.name}
                          </Text>
                          <Text
                            variant="caption"
                            color={theme.colors.textSecondary}
                          >
                            {table.rowCount} rows
                          </Text>
                        </View>
                      </TouchableOpacity>

                      {isExpanded && table.sampleRows.length > 0 && (
                        <View style={styles.tableData}>
                          <Text
                            variant="caption"
                            color={theme.colors.textSecondary}
                            style={{ marginBottom: 8 }}
                          >
                            {table.sampleRows.length < table.rowCount
                              ? `Showing first ${table.sampleRows.length} of ${table.rowCount} rows:`
                              : `All ${table.rowCount} rows:`}
                          </Text>
                          {table.sampleRows.map((row, idx) => (
                            <View key={idx} style={styles.rowContainer}>
                              <Text
                                variant="caption"
                                color={theme.colors.textSecondary}
                                style={{ marginBottom: 4 }}
                              >
                                Row {idx + 1}:
                              </Text>
                              {Object.entries(row).map(([key, value]) => (
                                <View key={key} style={styles.fieldRow}>
                                  <Text
                                    variant="caption"
                                    color={theme.colors.textSecondary}
                                    style={{ fontWeight: '600', minWidth: 100 }}
                                  >
                                    {key}:
                                  </Text>
                                  <Text
                                    variant="caption"
                                    color={theme.colors.text}
                                    style={styles.fieldValue}
                                    selectable
                                  >
                                    {formatValue(value)}
                                  </Text>
                                </View>
                              ))}
                            </View>
                          ))}
                        </View>
                      )}

                      {isExpanded && table.sampleRows.length === 0 && (
                        <View style={styles.tableData}>
                          <Text
                            variant="caption"
                            color={theme.colors.textSecondary}
                          >
                            Table is empty
                          </Text>
                        </View>
                      )}
                    </Card>
                  );
                })}
              </Box>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function formatValue(value: any): string {
  if (value === null || value === undefined) {
    return 'null';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '0 B';
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  const precision = value < 10 && unitIndex > 0 ? 1 : 0;
  return `${value.toFixed(precision)} ${units[unitIndex]}`;
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollView: { flex: 1 },
  scrollContent: { paddingBottom: 32 },
  backButton: {
    paddingVertical: 6,
    paddingRight: 12,
  },
  title: {
    marginTop: 8,
    fontWeight: 'normal',
  },
  statRow: {
    flexDirection: 'row',
    gap: 24,
  },
  statItem: {
    flex: 1,
  },
  pathText: {
    marginTop: 4,
    fontFamily: 'monospace',
  },
  tableHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tableData: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.1)',
  },
  rowContainer: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.05)',
  },
  fieldRow: {
    flexDirection: 'row',
    marginTop: 4,
  },
  fieldValue: {
    flex: 1,
    fontFamily: 'monospace',
  },
});

export default SQLiteDetailScreen;
