import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Search, X } from 'lucide-react-native';

import type { LearningStackParamList } from '../../../types';
import { CatalogUnitCard } from '../components/CatalogUnitCard';
import {
  useAddUnitToMyUnits,
  useRemoveUnitFromMyUnits,
  useUserUnitCollections,
  useCatalogUnits,
} from '../queries';
import type { Unit } from '../../content/public';
import { uiSystemProvider, Text } from '../../ui_system/public';
import { useAuth } from '../../user/public';

type CatalogBrowserNavigation = NativeStackNavigationProp<
  LearningStackParamList,
  'CatalogBrowser'
>;

export function CatalogBrowserScreen(): React.ReactElement {
  const navigation = useNavigation<CatalogBrowserNavigation>();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { user } = useAuth();
  const currentUserId = user?.id ?? 0;

  const [searchQuery, setSearchQuery] = useState('');

  const {
    data: collections,
    isLoading: isCollectionsLoading,
    isRefetching: isCollectionsRefetching,
    error: collectionsError,
  } = useUserUnitCollections(currentUserId, { includeGlobal: true });

  const {
    data: catalogUnits = [],
    isLoading: isCatalogLoading,
  } = useCatalogUnits({
    currentUserId,
  });

  const addMutation = useAddUnitToMyUnits();
  const removeMutation = useRemoveUnitFromMyUnits();
  const [pendingUnitId, setPendingUnitId] = useState<string | null>(null);

  const ownedUnitIds = useMemo(() => {
    const owned = collections?.ownedUnitIds ?? [];
    return new Set<string>(owned);
  }, [collections]);

  const myUnitIds = useMemo(() => {
    const ids = new Set<string>();
    for (const unit of collections?.units ?? []) {
      ids.add(unit.id);
    }
    return ids;
  }, [collections]);

  const globalUnits = useMemo(() => {
    return catalogUnits.filter(unit => unit.isGlobal);
  }, [catalogUnits]);

  const filteredUnits = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return globalUnits;
    }
    return globalUnits.filter(unit =>
      unit.title.toLowerCase().includes(query)
    );
  }, [globalUnits, searchQuery]);

  const isLoading = isCollectionsLoading || isCatalogLoading;

  const handleClose = useCallback(() => {
    navigation.goBack();
  }, [navigation]);

  const handleAdd = useCallback(
    (unit: Unit) => {
      if (!currentUserId) {
        return;
      }
      setPendingUnitId(unit.id);
      addMutation.mutate(
        { userId: currentUserId, unit },
        {
          onSettled: () => setPendingUnitId(null),
        }
      );
    },
    [addMutation, currentUserId]
  );

  const handleRemove = useCallback(
    (unit: Unit) => {
      if (!currentUserId) {
        return;
      }
      setPendingUnitId(unit.id);
      removeMutation.mutate(
        { userId: currentUserId, unit },
        {
          onSettled: () => setPendingUnitId(null),
        }
      );
    },
    [currentUserId, removeMutation]
  );

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      testID="catalog-browser-screen"
    >
      <View style={styles.header}>
        <Text variant="h1" weight="600">
          Browse Catalog
        </Text>
        <TouchableOpacity
          onPress={handleClose}
          style={styles.closeButton}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          testID="catalog-browser-close-button"
        >
          <X size={24} color={theme.colors.text} />
        </TouchableOpacity>
      </View>

      <View
        style={[
          styles.searchContainer,
          {
            backgroundColor: theme.colors.surface,
            borderColor: theme.colors.border,
          },
        ]}
      >
        <Search size={20} color={theme.colors.textSecondary} />
        <TextInput
          style={[styles.searchInput, { color: theme.colors.text }]}
          placeholder="Search catalog"
          placeholderTextColor={theme.colors.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCapitalize="none"
          autoCorrect={false}
          testID="catalog-browser-search-input"
        />
      </View>

      {collectionsError ? (
        <View style={styles.errorContainer}>
          <Text variant="secondary" color={theme.colors.error}>
            Unable to load catalog units. Pull to refresh.
          </Text>
        </View>
      ) : null}

      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator color={theme.colors.primary} size="large" />
        </View>
      ) : (
        <FlatList
          data={filteredUnits}
          keyExtractor={item => item.id}
          renderItem={({ item, index }) => {
            const isMember =
              myUnitIds.has(item.id) || ownedUnitIds.has(item.id);
            const isPending =
              pendingUnitId === item.id &&
              (addMutation.isPending || removeMutation.isPending);
            return (
              <CatalogUnitCard
                unit={item}
                index={index}
                isInMyUnits={isMember}
                onAdd={handleAdd}
                onRemove={handleRemove}
                isActionPending={isPending}
                disabled={!currentUserId || isCollectionsRefetching}
              />
            );
          }}
          ListEmptyComponent={() => (
            <View style={styles.emptyState}>
              <Search size={32} color={theme.colors.textSecondary} />
              <Text
                variant="title"
                weight="600"
                style={{ marginTop: ui.getSpacing('sm') }}
              >
                No units found
              </Text>
              <Text variant="secondary" color={theme.colors.textSecondary}>
                Try a different search term.
              </Text>
            </View>
          )}
          contentContainerStyle={
            filteredUnits.length === 0
              ? [styles.listContent, styles.listContentEmpty]
              : styles.listContent
          }
          keyboardShouldPersistTaps="handled"
          testID="catalog-browser-list"
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  closeButton: {
    padding: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 20,
    marginBottom: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    columnGap: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorContainer: {
    paddingHorizontal: 20,
    paddingBottom: 8,
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  listContentEmpty: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  emptyState: {
    alignItems: 'center',
    gap: 12,
  },
});
