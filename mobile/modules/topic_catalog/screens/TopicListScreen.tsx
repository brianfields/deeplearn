/**
 * TopicListScreen - Main topic browsing interface.
 *
 * Provides topic discovery, search, filtering, and navigation to learning sessions.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  SafeAreaView,
  RefreshControl,
  TextInput,
  TouchableOpacity,
  Modal,
  Alert,
} from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { Search, Filter, Loader, AlertCircle } from 'lucide-react-native';

import { TopicCard } from '../components/TopicCard';
import { SearchFilters } from '../components/SearchFilters';
import { useTopicCatalog, useRefreshCatalog } from '../queries';
import { TopicSummary, TopicFilters } from '../models';

interface TopicListScreenProps {
  onTopicPress: (topic: TopicSummary) => void;
}

export function TopicListScreen({ onTopicPress }: TopicListScreenProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<TopicFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  // Combined filters including search query
  const combinedFilters: TopicFilters = {
    ...filters,
    query: searchQuery.trim() || undefined,
  };

  // Data fetching
  const { topics, totalCount, isLoading, isError, error, refetch } =
    useTopicCatalog(combinedFilters);

  const refreshMutation = useRefreshCatalog();

  const handleRefresh = useCallback(async () => {
    try {
      await refreshMutation.mutateAsync();
      await refetch();
    } catch (error) {
      console.warn('Failed to refresh catalog:', error);
      Alert.alert(
        'Refresh Failed',
        'Could not refresh the topic catalog. Please try again.',
        [{ text: 'OK' }]
      );
    }
  }, [refreshMutation, refetch]);

  const handleTopicPress = useCallback(
    (topic: TopicSummary) => {
      onTopicPress(topic);
    },
    [onTopicPress]
  );

  const handleFiltersChange = useCallback((newFilters: TopicFilters) => {
    setFilters(newFilters);
  }, []);

  const renderTopic = useCallback(
    ({ item, index }: { item: TopicSummary; index: number }) => (
      <Animated.View
        entering={FadeIn.delay(index * 100)}
        style={styles.topicItemContainer}
      >
        <TopicCard
          topic={item}
          onPress={handleTopicPress}
          isOfflineAvailable={true} // TODO: Implement offline availability check
        />
      </Animated.View>
    ),
    [handleTopicPress]
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Search size={48} color="#9CA3AF" />
      <Text style={styles.emptyStateTitle}>No Topics Found</Text>
      <Text style={styles.emptyStateDescription}>
        {searchQuery || Object.keys(filters).length > 0
          ? 'Try adjusting your search or filters'
          : 'Pull down to refresh and load topics'}
      </Text>
    </View>
  );

  const renderErrorState = () => (
    <View style={styles.errorState}>
      <AlertCircle size={48} color="#EF4444" />
      <Text style={styles.errorStateTitle}>Failed to Load Topics</Text>
      <Text style={styles.errorStateDescription}>
        {error?.message || 'Please check your connection and try again'}
      </Text>
      <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
        <Text style={styles.retryButtonText}>Retry</Text>
      </TouchableOpacity>
    </View>
  );

  const renderLoadingState = () => (
    <View style={styles.loadingState}>
      <Loader size={48} color="#3B82F6" />
      <Text style={styles.loadingText}>Loading topics...</Text>
    </View>
  );

  if (isLoading && topics.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        {renderLoadingState()}
      </SafeAreaView>
    );
  }

  if (isError && topics.length === 0) {
    return (
      <SafeAreaView style={styles.container}>{renderErrorState()}</SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Learning Topics</Text>
        <Text style={styles.subtitle}>
          {totalCount > 0
            ? `${totalCount} topics available`
            : 'Discover new topics'}
        </Text>
      </View>

      {/* Search and Filter Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Search size={20} color="#9CA3AF" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search topics..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#9CA3AF"
          />
        </View>

        <TouchableOpacity
          style={[
            styles.filterButton,
            Object.keys(filters).length > 0 && styles.filterButtonActive,
          ]}
          onPress={() => setShowFilters(true)}
        >
          <Filter
            size={20}
            color={Object.keys(filters).length > 0 ? '#FFFFFF' : '#6B7280'}
          />
        </TouchableOpacity>
      </View>

      {/* Topic List */}
      <FlatList
        data={topics}
        renderItem={renderTopic}
        keyExtractor={item => item.id}
        contentContainerStyle={[
          styles.listContainer,
          topics.length === 0 && styles.listContainerEmpty,
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshMutation.isPending}
            onRefresh={handleRefresh}
            colors={['#3B82F6']}
            tintColor="#3B82F6"
          />
        }
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
        removeClippedSubviews={true}
        maxToRenderPerBatch={10}
        windowSize={10}
      />

      {/* Filter Modal */}
      <Modal
        visible={showFilters}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowFilters(false)}
      >
        <View style={styles.modalOverlay}>
          <SearchFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onClose={() => setShowFilters(false)}
          />
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 20,
    paddingBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
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
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
  },
  filterButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  filterButtonActive: {
    backgroundColor: '#3B82F6',
  },
  listContainer: {
    padding: 20,
    paddingTop: 0,
  },
  listContainerEmpty: {
    flex: 1,
    justifyContent: 'center',
  },
  topicItemContainer: {
    marginBottom: 0, // TopicCard has its own margin
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateDescription: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
  },
  errorState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  errorStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#EF4444',
    marginTop: 16,
    marginBottom: 8,
  },
  errorStateDescription: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  loadingState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 16,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
});
