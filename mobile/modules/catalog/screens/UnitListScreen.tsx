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
import { HardDrive, Plus, Search } from 'lucide-react-native';
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
import { useAuth, userIdentityProvider } from '../../user/public';
import { Button } from '../../ui_system/components/Button';
import { contentProvider } from '../../content/public';

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
  const { user, signOut } = useAuth();
  const identity = userIdentityProvider();
  const currentUserId = user?.id ?? 0;
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

  // Handle pull-to-refresh by forcing a full sync
  const handleRefresh = useCallback(async () => {
    try {
      const content = contentProvider();
      await content.syncNow(); // Force full sync, ignoring cursor
      await refetch(); // Then refresh the query
    } catch (error) {
      console.warn('[UnitListScreen] Sync failed on refresh:', error);
      // Still refetch to show cached data
      await refetch();
    }
  }, [refetch]);

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

  const handleOpenDownloads = useCallback(() => {
    haptics.trigger('light');
    navigation.navigate('CacheManagement');
  }, [navigation, haptics]);

  const handleRetryUnit = useCallback(
    (unitId: string) => {
      if (!currentUserId) {
        return;
      }
      retryUnitMutation.mutate(
        { unitId, ownerUserId: currentUserId },
        { onSuccess: () => refetch() }
      );
    },
    [retryUnitMutation, currentUserId, refetch]
  );

  const handleDismissUnit = useCallback(
    (unitId: string) => {
      if (!currentUserId) {
        return;
      }
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
      <View style={[styles.header, styles.headerRow]}>
        <View style={{ flex: 1 }}>
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
        <View style={styles.headerActions}>
          <Button
            title="Downloads"
            variant="secondary"
            size="small"
            onPress={handleOpenDownloads}
            testID="unit-list-cache-button"
            icon={<HardDrive size={16} color={theme.colors.primary} />}
          />
          <Button
            title="Sign out"
            variant="secondary"
            size="small"
            style={styles.headerActionSpacing}
            testID="unit-list-logout-button"
            onPress={async () => {
              haptics.trigger('light');
              await identity.clear();
              await signOut();
            }}
          />
        </View>
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
        onRefresh={handleRefresh}
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
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerActionSpacing: {
    marginLeft: 8,
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
