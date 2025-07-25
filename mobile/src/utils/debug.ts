/**
 * Debug utilities for development
 *
 * Helper functions for debugging and resetting app state
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { learningService } from '@/services/learning-service';
import { apiClient } from '@/services/api-client';

/**
 * Clear all AsyncStorage data
 */
export const clearAllStorage = async (): Promise<void> => {
  try {
    await AsyncStorage.clear();
    console.log('✅ All AsyncStorage data cleared');
  } catch (error) {
    console.error('❌ Failed to clear AsyncStorage:', error);
    throw error;
  }
};

/**
 * Clear only app-specific data (keeps system data)
 */
export const clearAppData = async (): Promise<void> => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const appKeys = keys.filter(
      key =>
        key.startsWith('learning_') ||
        key.startsWith('api_cache_') ||
        key.startsWith('duolingo_learning_')
    );

    if (appKeys.length > 0) {
      await AsyncStorage.multiRemove(appKeys);
      console.log(`✅ Cleared ${appKeys.length} app data entries`);
    } else {
      console.log('ℹ️ No app data found to clear');
    }
  } catch (error) {
    console.error('❌ Failed to clear app data:', error);
    throw error;
  }
};

/**
 * Clear learning progress and cache
 */
export const clearLearningData = async (): Promise<void> => {
  try {
    await learningService.clearCache();
    console.log('✅ Learning data cleared');
  } catch (error) {
    console.error('❌ Failed to clear learning data:', error);
    throw error;
  }
};

/**
 * Clear API cache
 */
export const clearApiCache = async (): Promise<void> => {
  try {
    await apiClient.clearCache();
    console.log('✅ API cache cleared');
  } catch (error) {
    console.error('❌ Failed to clear API cache:', error);
    throw error;
  }
};

/**
 * Reset all app data (progress + cache)
 */
export const resetAppState = async (): Promise<void> => {
  try {
    await Promise.all([clearLearningData(), clearApiCache()]);
    console.log('✅ App state reset complete');
  } catch (error) {
    console.error('❌ Failed to reset app state:', error);
    throw error;
  }
};

/**
 * Get storage statistics
 */
export const getStorageStats = async (): Promise<{
  totalKeys: number;
  appKeys: number;
  totalSize: number;
}> => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const appKeys = keys.filter(
      key =>
        key.startsWith('learning_') ||
        key.startsWith('api_cache_') ||
        key.startsWith('duolingo_learning_')
    );

    let totalSize = 0;
    for (const key of appKeys) {
      const value = await AsyncStorage.getItem(key);
      if (value) {
        totalSize += value.length;
      }
    }

    return {
      totalKeys: keys.length,
      appKeys: appKeys.length,
      totalSize,
    };
  } catch (error) {
    console.error('❌ Failed to get storage stats:', error);
    return { totalKeys: 0, appKeys: 0, totalSize: 0 };
  }
};

/**
 * Log all stored keys (for debugging)
 */
export const logStorageKeys = async (): Promise<void> => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    console.log('📱 AsyncStorage Keys:');
    keys.forEach(key => console.log(`  - ${key}`));

    const stats = await getStorageStats();
    console.log(`📊 Storage Stats:`);
    console.log(`  - Total keys: ${stats.totalKeys}`);
    console.log(`  - App keys: ${stats.appKeys}`);
    console.log(`  - Total size: ${stats.totalSize} characters`);
  } catch (error) {
    console.error('❌ Failed to log storage keys:', error);
  }
};
