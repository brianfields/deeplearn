/**
 * LessonListScreen - Main lesson browsing interface.
 *
 * Provides lesson discovery, search, filtering, and navigation to learning sessions.
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
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { LessonCard } from '../components/LessonCard';
import { SearchFilters } from '../components/SearchFilters';
import { useLessonCatalog, useRefreshCatalog } from '../queries';
import { LessonSummary, LessonFilters, LessonDetail } from '../models';
import type { LearningStackParamList } from '../../../types';

type LessonListScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'LessonList'
>;

export function LessonListScreen() {
  const navigation = useNavigation<LessonListScreenNavigationProp>();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<LessonFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  // Combined filters including search query
  const combinedFilters: LessonFilters = {
    ...filters,
    query: searchQuery.trim() || undefined,
  };

  // Data fetching
  const { lessons, totalCount, isLoading, isError, error, refetch } =
    useLessonCatalog(combinedFilters);

  const refreshMutation = useRefreshCatalog();

  const handleRefresh = useCallback(async () => {
    try {
      await refreshMutation.mutateAsync();
      await refetch();
    } catch (error) {
      console.warn('Failed to refresh catalog:', error);
      Alert.alert(
        'Refresh Failed',
        'Could not refresh the lesson catalog. Please try again.',
        [{ text: 'OK' }]
      );
    }
  }, [refreshMutation, refetch]);

  const handleLessonPress = useCallback(
    (lesson: LessonSummary) => {
      // Convert LessonSummary to LessonDetail for navigation
      const lessonDetail: LessonDetail = {
        id: lesson.id,
        title: lesson.title,
        coreConcept: lesson.coreConcept,
        userLevel: lesson.userLevel,
        learningObjectives: lesson.learningObjectives,
        keyConcepts: lesson.keyConcepts,
        components: [], // Will be fetched by LearningFlow if needed
        componentCount: lesson.componentCount,
        createdAt: lesson.createdAt || new Date().toISOString(),
        estimatedDuration: lesson.estimatedDuration,
        isReadyForLearning: lesson.isReadyForLearning,
        difficultyLevel: lesson.difficultyLevel,
        durationDisplay: lesson.durationDisplay,
        readinessStatus: lesson.readinessStatus,
        tags: lesson.tags,
      };

      navigation.navigate('LearningFlow', {
        lessonId: lesson.id,
        lesson: lessonDetail,
      });
    },
    [navigation]
  );

  const handleFiltersChange = useCallback((newFilters: LessonFilters) => {
    setFilters(newFilters);
  }, []);

  const renderLesson = useCallback(
    ({ item, index }: { item: LessonSummary; index: number }) => (
      <Animated.View
        entering={FadeIn.delay(index * 100)}
        style={styles.lessonItemContainer}
      >
        <LessonCard
          lesson={item}
          onPress={handleLessonPress}
          isOfflineAvailable={true} // TODO: Implement offline availability check
        />
      </Animated.View>
    ),
    [handleLessonPress]
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Search size={48} color="#9CA3AF" />
      <Text style={styles.emptyStateTitle}>No Lessons Found</Text>
      <Text style={styles.emptyStateDescription}>
        {searchQuery || Object.keys(filters).length > 0
          ? 'Try adjusting your search or filters'
          : 'Pull down to refresh and load lessons'}
      </Text>
    </View>
  );

  const renderErrorState = () => (
    <View style={styles.errorState}>
      <AlertCircle size={48} color="#EF4444" />
      <Text style={styles.errorStateTitle}>Failed to Load Lessons</Text>
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
      <Text style={styles.loadingText}>Loading lessons...</Text>
    </View>
  );

  if (isLoading && lessons.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        {renderLoadingState()}
      </SafeAreaView>
    );
  }

  if (isError && lessons.length === 0) {
    return (
      <SafeAreaView style={styles.container}>{renderErrorState()}</SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Learning Lessons</Text>
        <Text style={styles.subtitle}>
          {totalCount > 0
            ? `${totalCount} lessons available`
            : 'Discover new lessons'}
        </Text>
      </View>

      {/* Search and Filter Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Search size={20} color="#9CA3AF" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search lessons..."
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

      {/* Lesson List */}
      <FlatList
        data={lessons}
        renderItem={renderLesson}
        keyExtractor={item => item.id}
        contentContainerStyle={[
          styles.listContainer,
          lessons.length === 0 && styles.listContainerEmpty,
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
  lessonItemContainer: {
    marginBottom: 0, // LessonCard has its own margin
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
