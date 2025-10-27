/**
 * AsyncStorageDetailScreen - Detailed AsyncStorage Information
 *
 * Shows complete key-value pairs stored in AsyncStorage.
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
import AsyncStorage from '@react-native-async-storage/async-storage';
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
import type { LearningStackParamList } from '../../../types';

type AsyncStorageDetailNavigation = NativeStackNavigationProp<
  LearningStackParamList,
  'AsyncStorageDetail'
>;

interface AsyncStorageItem {
  key: string;
  value: string;
  size: number;
}

interface AsyncStorageInfo {
  keys: number;
  estimatedSize: number;
  items: AsyncStorageItem[];
  loading: boolean;
}

export function AsyncStorageDetailScreen(): React.ReactElement {
  const navigation = useNavigation<AsyncStorageDetailNavigation>();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const [asyncInfo, setAsyncInfo] = useState<AsyncStorageInfo>({
    keys: 0,
    estimatedSize: 0,
    items: [],
    loading: true,
  });

  const loadAsyncStorageInfo = useCallback(async () => {
    setAsyncInfo(prev => ({ ...prev, loading: true }));

    try {
      let asyncKeys = 0;
      let asyncEstimatedSize = 0;
      const asyncItems: AsyncStorageItem[] = [];

      try {
        const keys = await AsyncStorage.getAllKeys();
        asyncKeys = keys.length;

        // Get all key-value pairs
        const allData = await AsyncStorage.multiGet(keys);
        for (const [key, value] of allData) {
          const valueStr = value || '';
          const itemSize = (key?.length || 0) + valueStr.length;
          asyncEstimatedSize += itemSize;
          asyncItems.push({
            key: key || '',
            value: valueStr,
            size: itemSize,
          });
        }

        // Sort by size (largest first)
        asyncItems.sort((a, b) => b.size - a.size);
      } catch (error) {
        console.warn(
          '[AsyncStorageDetail] Failed to get AsyncStorage info:',
          error
        );
      }

      setAsyncInfo({
        keys: asyncKeys,
        estimatedSize: asyncEstimatedSize,
        items: asyncItems,
        loading: false,
      });
    } catch (error) {
      console.error(
        '[AsyncStorageDetail] Failed to load AsyncStorage info:',
        error
      );
      setAsyncInfo(prev => ({ ...prev, loading: false }));
    }
  }, []);

  useEffect(() => {
    loadAsyncStorageInfo();
  }, [loadAsyncStorageInfo]);

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
            AsyncStorage
          </Text>
          <Text variant="secondary" color={theme.colors.textSecondary}>
            All key-value pairs
          </Text>
        </Box>

        {asyncInfo.loading ? (
          <Box p="lg">
            <ActivityIndicator size="large" color={theme.colors.primary} />
          </Box>
        ) : (
          <>
            <Box px="lg" mb="md">
              <Card variant="default">
                <View style={styles.statRow}>
                  <View style={styles.statItem}>
                    <Text
                      variant="secondary"
                      color={theme.colors.textSecondary}
                    >
                      Keys
                    </Text>
                    <Text variant="h2" color={theme.colors.primary}>
                      {asyncInfo.keys}
                    </Text>
                  </View>
                  <View style={styles.statItem}>
                    <Text
                      variant="secondary"
                      color={theme.colors.textSecondary}
                    >
                      Total Size
                    </Text>
                    <Text variant="h2" color={theme.colors.primary}>
                      {formatBytes(asyncInfo.estimatedSize)}
                    </Text>
                  </View>
                </View>
              </Card>
            </Box>

            <Box px="lg" mb="md">
              <Button
                title="Refresh"
                variant="secondary"
                size="medium"
                fullWidth
                onPress={() => {
                  haptics.trigger('light');
                  loadAsyncStorageInfo();
                }}
                testID="refresh-async-storage"
              />
            </Box>

            {asyncInfo.items.length === 0 ? (
              <Box px="lg">
                <Card variant="outlined">
                  <Text variant="body" color={theme.colors.textSecondary}>
                    No data in AsyncStorage
                  </Text>
                </Card>
              </Box>
            ) : (
              <Box px="lg">
                <Text variant="title" style={{ marginBottom: 12 }}>
                  All Keys & Values
                </Text>
                {asyncInfo.items.map((item, index) => (
                  <Card
                    key={item.key}
                    variant="outlined"
                    style={{ marginBottom: 12 }}
                  >
                    <View style={styles.itemHeader}>
                      <Text
                        variant="body"
                        style={{ fontWeight: '600', flex: 1, marginRight: 8 }}
                      >
                        {item.key}
                      </Text>
                      <Text
                        variant="caption"
                        color={theme.colors.textSecondary}
                      >
                        {formatBytes(item.size)}
                      </Text>
                    </View>
                    <Text
                      variant="caption"
                      color={theme.colors.textSecondary}
                      style={styles.itemValue}
                      selectable
                    >
                      {item.value}
                    </Text>
                  </Card>
                ))}
              </Box>
            )}
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
  statRow: {
    flexDirection: 'row',
    gap: 24,
  },
  statItem: {
    flex: 1,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  itemValue: {
    fontFamily: 'monospace',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.1)',
  },
});

export default AsyncStorageDetailScreen;
