/**
 * LessonListScreen - Updated to show Units
 *
 * Displays available units for browsing, with search and navigation to UnitDetail.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  TextInput,
  TouchableOpacity,
  SectionList,
} from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { reducedMotion } from '../../ui_system/utils/motion';
import { animationTimings } from '../../ui_system/utils/animations';
import { Search, Plus } from 'lucide-react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { UnitCard } from '../components/UnitCard';
import {
  useUserUnitCollections,
  useRetryUnitCreation,
  useDismissUnit,
} from '../queries';
import type { Unit } from '../public';
import type { LearningStackParamList } from '../../../types';
import { uiSystemProvider, Text, useHaptics } from '../../ui_system/public';

type LessonListScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'LessonList'
>;

type UnitSection = {
  title: string;
  data: Unit[];
  emptyMessage: string;
};

export function LessonListScreen() {
  const navigation = useNavigation<LessonListScreenNavigationProp>();
  const [searchQuery, setSearchQuery] = useState('');
  const currentUserId = 1; // TODO: replace with authenticated user context
  const {
    data: collections,
    isLoading,
    refetch,
  } = useUserUnitCollections(currentUserId, { includeGlobal: true });
  const retryUnitMutation = useRetryUnitCreation();
  const dismissUnitMutation = useDismissUnit();
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();

  const personalUnits = collections?.personalUnits ?? [];
  const globalUnits = collections?.globalUnits ?? [];
  const totalUnits = personalUnits.length + globalUnits.length;

  const matchesSearch = (unit: Unit) =>
    !searchQuery.trim() ||
    unit.title.toLowerCase().includes(searchQuery.trim().toLowerCase());

  const filteredPersonalUnits = personalUnits.filter(matchesSearch);
  const filteredGlobalUnits = globalUnits.filter(matchesSearch);

  const sections: UnitSection[] = [
    {
      title: 'My Units',
      data: filteredPersonalUnits,
      emptyMessage: searchQuery
        ? 'No personal units match your search.'
        : 'Create a unit to see it here.',
    },
    {
      title: 'Global Units',
      data: filteredGlobalUnits,
      emptyMessage: searchQuery
        ? 'No shared units match your search.'
        : 'Shared units from other learners appear here.',
    },
  ];

  const hasResults =
    filteredPersonalUnits.length > 0 || filteredGlobalUnits.length > 0;

  const handleUnitPress = useCallback(
    (unit: Unit) => {
      navigation.navigate('UnitDetail', { unitId: unit.id });
    },
    [navigation]
  );

  const handleCreateUnit = useCallback(() => {
    haptics.trigger('medium');
    navigation.navigate('CreateUnit');
  }, [navigation, haptics]);

  const handleRetryUnit = useCallback(
    (unitId: string) => {
      retryUnitMutation.mutate(
        { unitId, ownerUserId: currentUserId },
        { onSuccess: () => refetch() }
      );
    },
    [retryUnitMutation, currentUserId, refetch]
  );

  const handleDismissUnit = useCallback(
    (unitId: string) => {
      dismissUnitMutation.mutate(
        { unitId, ownerUserId: currentUserId },
        { onSuccess: () => refetch() }
      );
    },
    [dismissUnitMutation, currentUserId, refetch]
  );

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text
          variant="h1"
          testID="units-title"
          style={{ fontWeight: 'normal' }}
        >
          Units
        </Text>
        <Text variant="secondary" color={theme.colors.textSecondary}>
          {totalUnits} available
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
          style={[
            styles.createButton,
            { backgroundColor: theme.colors.primary },
            ui.getDesignSystem().shadows.medium as any,
          ]}
          onPress={handleCreateUnit}
          testID="create-unit-button"
        >
          <Plus size={20} color={theme.colors.surface} />
        </TouchableOpacity>
      </View>

      {/* Unit Sections */}
      <SectionList<Unit, UnitSection>
        sections={sections}
        keyExtractor={item => item.id}
        renderItem={({ item, index, section }) => {
          const overallIndex =
            section.title === 'Global Units'
              ? filteredPersonalUnits.length + index
              : index;
          return (
            <Animated.View
              entering={
                reducedMotion.enabled
                  ? undefined
                  : FadeIn.duration(animationTimings.ui).delay(
                      overallIndex * animationTimings.stagger
                    )
              }
              style={styles.listItemContainer}
            >
              <UnitCard
                unit={item}
                onPress={handleUnitPress}
                onRetry={handleRetryUnit}
                onDismiss={handleDismissUnit}
                index={overallIndex}
              />
            </Animated.View>
          );
        }}
        renderSectionHeader={({ section }) => (
          <Text variant="title" style={styles.sectionHeader}>
            {section.title}
          </Text>
        )}
        renderSectionFooter={({ section }) =>
          section.data.length === 0 ? (
            <Text
              variant="secondary"
              color={theme.colors.textSecondary}
              style={styles.sectionFooter}
            >
              {section.emptyMessage}
            </Text>
          ) : null
        }
        contentContainerStyle={[
          styles.listContainer,
          !hasResults && styles.listContainerEmpty,
        ]}
        refreshing={isLoading}
        onRefresh={() => refetch()}
        ListFooterComponent={() =>
          hasResults ? null : (
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
          )
        }
        stickySectionHeadersEnabled={false}
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
    alignItems: 'center',
    justifyContent: 'center',
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
  sectionHeader: {
    marginTop: 24,
    marginBottom: 12,
  },
  sectionFooter: {
    marginBottom: 16,
  },
});
