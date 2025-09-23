/**
 * LessonListScreen - Updated to show Units
 *
 * Displays available units for browsing, with search and navigation to UnitDetail.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  SafeAreaView,
  TextInput,
  TouchableOpacity,
} from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { Search, Plus } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { UnitCard } from '../components/UnitCard';
import {
  useCatalogUnits,
  useRetryUnitCreation,
  useDismissUnit,
} from '../queries';
import type { Unit } from '../public';
import type { LearningStackParamList } from '../../../types';
import { uiSystemProvider, Text } from '../../ui_system/public';

type LessonListScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'LessonList'
>;

export function LessonListScreen() {
  const navigation = useNavigation<LessonListScreenNavigationProp>();
  const [searchQuery, setSearchQuery] = useState('');
  const { data: units = [], isLoading, refetch } = useCatalogUnits();
  const retryUnitMutation = useRetryUnitCreation();
  const dismissUnitMutation = useDismissUnit();
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();

  const filteredUnits = units.filter(
    u =>
      !searchQuery.trim() ||
      u.title.toLowerCase().includes(searchQuery.trim().toLowerCase())
  );

  const handleUnitPress = useCallback(
    (unit: Unit) => {
      navigation.navigate('UnitDetail', { unitId: unit.id });
    },
    [navigation]
  );

  const handleCreateUnit = useCallback(() => {
    navigation.navigate('CreateUnit');
  }, [navigation]);

  const handleRetryUnit = useCallback(
    (unitId: string) => {
      retryUnitMutation.mutate(unitId);
    },
    [retryUnitMutation]
  );

  const handleDismissUnit = useCallback(
    (unitId: string) => {
      dismissUnitMutation.mutate(unitId);
    },
    [dismissUnitMutation]
  );

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text variant="h1" testID="units-title">
          Units
        </Text>
        <Text variant="secondary" color={theme.colors.textSecondary}>
          {units.length} available
        </Text>
      </View>

      {/* Search and Create Button */}
      <View style={styles.searchContainer}>
        <View
          style={[
            styles.searchInputContainer,
            {
              backgroundColor: theme.colors.surface,
              borderWidth: StyleSheet.hairlineWidth,
              borderColor: isSearchFocused
                ? theme.colors.secondary
                : theme.colors.border,
              shadowOpacity: 0,
              elevation: 0,
              borderRadius: 20,
              minHeight: 44,
            },
          ]}
        >
          <Search
            size={20}
            color={theme.colors.textSecondary}
            style={styles.searchIcon}
          />
          <TextInput
            style={[styles.searchInput, { color: theme.colors.text }]}
            placeholder="Search units..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor={theme.colors.textSecondary}
            onFocus={() => setIsSearchFocused(true)}
            onBlur={() => setIsSearchFocused(false)}
            testID="search-input"
          />
        </View>
        <TouchableOpacity
          style={styles.createButton}
          onPress={handleCreateUnit}
          testID="create-unit-button"
        >
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Unit List */}
      <FlatList
        data={filteredUnits}
        renderItem={({ item, index }) => (
          <Animated.View
            entering={FadeIn.delay(index * 24)}
            style={styles.listItemContainer}
          >
            <UnitCard
              unit={item}
              onPress={handleUnitPress}
              onRetry={handleRetryUnit}
              onDismiss={handleDismissUnit}
              index={index}
            />
          </Animated.View>
        )}
        keyExtractor={item => item.id}
        contentContainerStyle={[
          styles.listContainer,
          filteredUnits.length === 0 && styles.listContainerEmpty,
        ]}
        refreshing={isLoading}
        onRefresh={() => refetch()}
        ListEmptyComponent={() => (
          <View style={styles.emptyState}>
            <Search size={48} color={theme.colors.textSecondary} />
            <Text variant="title" style={{ marginTop: 16 }}>
              No Units Found
            </Text>
            <Text variant="body" color={theme.colors.textSecondary}>
              {searchQuery
                ? 'Try adjusting your search'
                : 'Pull down to refresh'}
            </Text>
          </View>
        )}
        showsVerticalScrollIndicator={false}
        removeClippedSubviews={true}
        maxToRenderPerBatch={10}
        windowSize={10}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingBottom: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 16,
    gap: 12,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  createButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
  listContainer: {
    padding: 20,
    paddingTop: 0,
  },
  listContainerEmpty: {
    flex: 1,
    justifyContent: 'center',
  },
  listItemContainer: {
    marginBottom: 0,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
});
