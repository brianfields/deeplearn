/**
 * ManageCacheScreen - Dev Tool for Cache Management
 *
 * Shows storage summary with clickable cards to view details.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import * as FileSystem from 'expo-file-system';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useQueryClient } from '@tanstack/react-query';
import { ChevronRight } from 'lucide-react-native';

import {
  Box,
  Card,
  Text,
  Button,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { offlineCacheProvider } from '../public';
import { infrastructureProvider } from '../../infrastructure/public';
import type { LearningStackParamList } from '../../../types';

type ManageCacheNavigation = NativeStackNavigationProp<
  LearningStackParamList,
  'ManageCache'
>;

interface StorageSummary {
  sqlite: {
    dbSize: number;
  };
  asyncStorage: {
    keys: number;
    estimatedSize: number;
  };
  fileSystem: {
    totalSize: number;
    files: number;
  };
  loading: boolean;
}

export function ManageCacheScreen(): React.ReactElement {
  const navigation = useNavigation<ManageCacheNavigation>();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const queryClient = useQueryClient();
  const [summary, setSummary] = useState<StorageSummary>({
    sqlite: { dbSize: 0 },
    asyncStorage: { keys: 0, estimatedSize: 0 },
    fileSystem: { totalSize: 0, files: 0 },
    loading: true,
  });
  const [isClearing, setIsClearing] = useState(false);
  const [isClearingKeepLogin, setIsClearingKeepLogin] = useState(false);

  const USER_STORAGE_KEY = 'deeplearn/mobile/current-user';

  const loadSummary = useCallback(async () => {
    setSummary(prev => ({ ...prev, loading: true }));

    try {
      // Get SQLite info
      const infra = infrastructureProvider();
      const sqliteProvider = await infra.createSQLiteProvider({
        databaseName: 'offline_unit_cache.db',
        enableForeignKeys: true,
        migrations: [],
      });

      let dbSize = 0;
      try {
        const dbInfo = await sqliteProvider.getDatabaseInfo();
        if (dbInfo.path) {
          const fileInfo = await FileSystem.getInfoAsync(dbInfo.path);
          if (fileInfo.exists) {
            dbSize = fileInfo.size || 0;
          }
        }
      } catch (error) {
        console.warn('[ManageCache] Failed to get SQLite info:', error);
      }

      // Get AsyncStorage info
      let asyncKeys = 0;
      let asyncEstimatedSize = 0;
      try {
        const keys = await AsyncStorage.getAllKeys();
        asyncKeys = keys.length;

        const allData = await AsyncStorage.multiGet(keys);
        for (const [key, value] of allData) {
          const itemSize = (key?.length || 0) + (value?.length || 0);
          asyncEstimatedSize += itemSize;
        }
      } catch (error) {
        console.warn('[ManageCache] Failed to get AsyncStorage info:', error);
      }

      // Get file system info - enumerate actual files on disk
      let totalFileSize = 0;
      let fileCount = 0;
      let dbTrackedFiles = 0;
      let orphanedFiles = 0;
      const cacheDir = (FileSystem.documentDirectory ?? 'file://documents')
        .replace(/\/$/, '')
        .concat('/offline-cache');

      try {
        const dirInfo = await FileSystem.getInfoAsync(cacheDir);
        if (dirInfo.exists) {
          console.log('[ManageCache] Cache directory exists:', cacheDir);

          // Get list of files tracked by the database
          const offlineCache = offlineCacheProvider();
          const units = await offlineCache.listDownloadedUnits();
          const trackedPaths = new Set<string>();

          for (const unit of units) {
            const unitDetail = await offlineCache.getUnitDetail(unit.id);
            if (unitDetail?.assets) {
              for (const asset of unitDetail.assets) {
                if (asset.localPath && asset.status === 'completed') {
                  trackedPaths.add(asset.localPath);
                  dbTrackedFiles++;
                }
              }
            }
          }

          // Now enumerate actual files on disk
          try {
            const files = await FileSystem.readDirectoryAsync(cacheDir);
            console.log(`[ManageCache] Found ${files.length} files on disk`);

            for (const filename of files) {
              const filePath = `${cacheDir}/${filename}`;
              try {
                const fileInfo = await FileSystem.getInfoAsync(filePath);
                if (fileInfo.exists && !fileInfo.isDirectory) {
                  fileCount++;
                  if ('size' in fileInfo) {
                    totalFileSize += fileInfo.size || 0;
                  }

                  // Check if this file is tracked by the database
                  if (!trackedPaths.has(filePath)) {
                    orphanedFiles++;
                    console.warn('[ManageCache] Orphaned file found:', {
                      filename,
                      path: filePath,
                      size: 'size' in fileInfo ? fileInfo.size : 'unknown',
                    });
                  }
                }
              } catch (err) {
                console.warn(
                  '[ManageCache] Failed to stat file:',
                  filename,
                  err
                );
              }
            }

            console.log('[ManageCache] File system summary:', {
              filesOnDisk: fileCount,
              filesInDatabase: dbTrackedFiles,
              orphanedFiles,
              totalFileSize,
              totalFileSizeMB: (totalFileSize / (1024 * 1024)).toFixed(2),
            });
          } catch (err) {
            console.warn('[ManageCache] Failed to read directory:', err);
            // Fall back to database-only count
            fileCount = dbTrackedFiles;
          }
        }
      } catch (error) {
        console.warn('[ManageCache] Failed to get file system info:', error);
      }

      setSummary({
        sqlite: { dbSize },
        asyncStorage: { keys: asyncKeys, estimatedSize: asyncEstimatedSize },
        fileSystem: { totalSize: totalFileSize, files: fileCount },
        loading: false,
      });
    } catch (error) {
      console.error('[ManageCache] Failed to load summary:', error);
      setSummary(prev => ({ ...prev, loading: false }));
    }
  }, []);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const handleClearData = useCallback(() => {
    Alert.alert(
      'Clear All Data',
      'This will delete all cached content, including:\n\n• Downloaded units and lessons\n• Offline cache database\n• App preferences\n• React Query cache\n\nYou will need to re-download everything and log in again.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All Data',
          style: 'destructive',
          onPress: async () => {
            setIsClearing(true);
            haptics.trigger('medium');

            try {
              // 1. Clear offline cache (SQLite and files)
              const offlineCache = offlineCacheProvider();
              await offlineCache.clearAll();

              // 2. Clear AsyncStorage
              await AsyncStorage.clear();

              // 3. Clear React Query cache
              queryClient.clear();

              // 4. Reload summary
              await loadSummary();

              haptics.trigger('success');
              Alert.alert(
                'Data Cleared',
                'All cached data has been removed successfully.'
              );
            } catch (error) {
              console.error('[ManageCache] Failed to clear data:', error);
              haptics.trigger('light');
              Alert.alert(
                'Clear Failed',
                'Failed to clear all data. Some data may remain.'
              );
            } finally {
              setIsClearing(false);
            }
          },
        },
      ]
    );
  }, [haptics, loadSummary, queryClient]);

  const handleClearKeepLogin = useCallback(() => {
    Alert.alert(
      'Clear Cache (Keep Login)',
      'This will delete all cached content except your login:\n\n• Downloaded units and lessons\n• Offline cache database\n• Most app preferences\n• React Query cache\n\nYou will stay logged in but need to re-download content.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear Cache',
          style: 'destructive',
          onPress: async () => {
            setIsClearingKeepLogin(true);
            haptics.trigger('medium');

            try {
              // 1. Clear offline cache (SQLite and files)
              const offlineCache = offlineCacheProvider();
              await offlineCache.clearAll();

              // 2. Selectively clear AsyncStorage (keep user login)
              const allKeys = await AsyncStorage.getAllKeys();
              const keysToRemove = allKeys.filter(
                key => key !== USER_STORAGE_KEY
              );

              console.log('[ManageCache] Clearing AsyncStorage keys:', {
                total: allKeys.length,
                removing: keysToRemove.length,
                keeping: [USER_STORAGE_KEY],
              });

              if (keysToRemove.length > 0) {
                await AsyncStorage.multiRemove(keysToRemove);
              }

              // 3. Clear React Query cache
              queryClient.clear();

              // 4. Reload summary
              await loadSummary();

              haptics.trigger('success');
              Alert.alert(
                'Cache Cleared',
                'Cached data removed. You are still logged in.'
              );
            } catch (error) {
              console.error('[ManageCache] Failed to clear cache:', error);
              haptics.trigger('light');
              Alert.alert(
                'Clear Failed',
                'Failed to clear cache. Some data may remain.'
              );
            } finally {
              setIsClearingKeepLogin(false);
            }
          },
        },
      ]
    );
  }, [haptics, loadSummary, queryClient, USER_STORAGE_KEY]);

  const totalStorageBytes =
    summary.sqlite.dbSize +
    summary.asyncStorage.estimatedSize +
    summary.fileSystem.totalSize;

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
          <Text variant="h1" style={styles.title}>
            Manage Cache
          </Text>
          <Text variant="secondary" color={theme.colors.textSecondary}>
            Developer tool for inspecting and clearing storage
          </Text>
        </Box>

        {summary.loading ? (
          <Box p="lg">
            <ActivityIndicator size="large" color={theme.colors.primary} />
          </Box>
        ) : (
          <>
            {/* Total Storage */}
            <Box px="lg" mb="md">
              <Card variant="default">
                <Text variant="title" style={localStyles.marginBottom8}>
                  Total Storage Used
                </Text>
                <Text variant="h2" color={theme.colors.primary}>
                  {formatBytes(totalStorageBytes)}
                </Text>
              </Card>
            </Box>

            {/* SQLite - Clickable */}
            <Box px="lg" mb="md">
              <TouchableOpacity
                onPress={() => {
                  haptics.trigger('light');
                  navigation.navigate('SQLiteDetail');
                }}
                activeOpacity={0.7}
              >
                <Card variant="outlined">
                  <View style={styles.cardHeader}>
                    <Text variant="title">SQLite Database</Text>
                    <ChevronRight
                      size={20}
                      color={theme.colors.textSecondary}
                    />
                  </View>
                  <Text
                    variant="h2"
                    color={theme.colors.primary}
                    style={localStyles.marginTop8}
                  >
                    {formatBytes(summary.sqlite.dbSize)}
                  </Text>
                </Card>
              </TouchableOpacity>
            </Box>

            {/* AsyncStorage - Clickable */}
            <Box px="lg" mb="md">
              <TouchableOpacity
                onPress={() => {
                  haptics.trigger('light');
                  navigation.navigate('AsyncStorageDetail');
                }}
                activeOpacity={0.7}
              >
                <Card variant="outlined">
                  <View style={styles.cardHeader}>
                    <Text variant="title">AsyncStorage</Text>
                    <ChevronRight
                      size={20}
                      color={theme.colors.textSecondary}
                    />
                  </View>
                  <View style={styles.statRow}>
                    <View style={styles.statItem}>
                      <Text
                        variant="secondary"
                        color={theme.colors.textSecondary}
                      >
                        Keys
                      </Text>
                      <Text variant="h2" color={theme.colors.primary}>
                        {summary.asyncStorage.keys}
                      </Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text
                        variant="secondary"
                        color={theme.colors.textSecondary}
                      >
                        Size
                      </Text>
                      <Text variant="h2" color={theme.colors.primary}>
                        {formatBytes(summary.asyncStorage.estimatedSize)}
                      </Text>
                    </View>
                  </View>
                </Card>
              </TouchableOpacity>
            </Box>

            {/* File System - Clickable */}
            <Box px="lg" mb="md">
              <TouchableOpacity
                onPress={() => {
                  haptics.trigger('light');
                  navigation.navigate('FileSystemDetail');
                }}
                activeOpacity={0.7}
              >
                <Card variant="outlined">
                  <View style={styles.cardHeader}>
                    <Text variant="title">File System</Text>
                    <ChevronRight
                      size={20}
                      color={theme.colors.textSecondary}
                    />
                  </View>
                  <View style={styles.statRow}>
                    <View style={styles.statItem}>
                      <Text
                        variant="secondary"
                        color={theme.colors.textSecondary}
                      >
                        Files
                      </Text>
                      <Text variant="h2" color={theme.colors.primary}>
                        {summary.fileSystem.files}
                      </Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text
                        variant="secondary"
                        color={theme.colors.textSecondary}
                      >
                        Size
                      </Text>
                      <Text variant="h2" color={theme.colors.primary}>
                        {formatBytes(summary.fileSystem.totalSize)}
                      </Text>
                    </View>
                  </View>
                </Card>
              </TouchableOpacity>
            </Box>

            {/* Actions */}
            <Box px="lg" mb="md">
              <Button
                title="Refresh"
                variant="secondary"
                size="medium"
                fullWidth
                onPress={() => {
                  haptics.trigger('light');
                  loadSummary();
                }}
                disabled={summary.loading}
                testID="refresh-storage-info"
              />
            </Box>

            <Box px="lg" mb="md">
              <Button
                title={
                  isClearingKeepLogin
                    ? 'Clearing...'
                    : 'Clear Cache (Keep Login)'
                }
                variant="secondary"
                size="large"
                fullWidth
                onPress={handleClearKeepLogin}
                disabled={isClearingKeepLogin || isClearing || summary.loading}
                testID="clear-cache-keep-login"
              />
            </Box>

            <Box px="lg" mb="lg">
              <Button
                title={isClearing ? 'Clearing...' : 'Clear All Data'}
                variant="primary"
                size="large"
                fullWidth
                onPress={handleClearData}
                disabled={isClearing || isClearingKeepLogin || summary.loading}
                testID="clear-all-data"
              />
            </Box>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
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
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statRow: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 24,
  },
  statItem: {
    flex: 1,
  },
});

const localStyles = StyleSheet.create({
  marginBottom8: {
    marginBottom: 8,
  },
  marginTop8: {
    marginTop: 8,
  },
});

export default ManageCacheScreen;
