/**
 * SearchFilters component for lesson catalog.
 *
 * Provides UI controls for filtering and sorting lessons.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { X, Check } from 'lucide-react-native';

import { LessonFilters } from '../models';

interface SearchFiltersProps {
  filters: LessonFilters;
  onFiltersChange: (filters: LessonFilters) => void;
  onClose?: () => void;
}

export function SearchFilters({
  filters,
  onFiltersChange,
  onClose,
}: SearchFiltersProps) {
  const [localFilters, setLocalFilters] = useState<LessonFilters>(filters);

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    onClose?.();
  };

  const handleClearFilters = () => {
    const clearedFilters: LessonFilters = {};
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
    onClose?.();
  };

  const updateFilter = <K extends keyof LessonFilters>(
    key: K,
    value: LessonFilters[K]
  ) => {
    setLocalFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Filter Lessons</Text>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color="#6B7280" />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView style={styles.content}>
        {/* User Level Filter */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Difficulty Level</Text>
          <View style={styles.optionGroup}>
            {(['beginner', 'intermediate', 'advanced'] as const).map(level => (
              <TouchableOpacity
                key={level}
                style={[
                  styles.option,
                  localFilters.userLevel === level && styles.optionSelected,
                ]}
                onPress={() =>
                  updateFilter(
                    'userLevel',
                    localFilters.userLevel === level ? undefined : level
                  )
                }
              >
                <Text
                  style={[
                    styles.optionText,
                    localFilters.userLevel === level &&
                      styles.optionTextSelected,
                  ]}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </Text>
                {localFilters.userLevel === level && (
                  <Check size={16} color="#FFFFFF" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Duration Filter */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Duration</Text>
          <View style={styles.optionGroup}>
            <TouchableOpacity
              style={[
                styles.option,
                localFilters.maxDuration === 15 && styles.optionSelected,
              ]}
              onPress={() =>
                updateFilter(
                  'maxDuration',
                  localFilters.maxDuration === 15 ? undefined : 15
                )
              }
            >
              <Text
                style={[
                  styles.optionText,
                  localFilters.maxDuration === 15 && styles.optionTextSelected,
                ]}
              >
                Quick (≤15 min)
              </Text>
              {localFilters.maxDuration === 15 && (
                <Check size={16} color="#FFFFFF" />
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.option,
                localFilters.minDuration === 16 &&
                  localFilters.maxDuration === 30 &&
                  styles.optionSelected,
              ]}
              onPress={() => {
                if (
                  localFilters.minDuration === 16 &&
                  localFilters.maxDuration === 30
                ) {
                  updateFilter('minDuration', undefined);
                  updateFilter('maxDuration', undefined);
                } else {
                  updateFilter('minDuration', 16);
                  updateFilter('maxDuration', 30);
                }
              }}
            >
              <Text
                style={[
                  styles.optionText,
                  localFilters.minDuration === 16 &&
                    localFilters.maxDuration === 30 &&
                    styles.optionTextSelected,
                ]}
              >
                Medium (16-30 min)
              </Text>
              {localFilters.minDuration === 16 &&
                localFilters.maxDuration === 30 && (
                  <Check size={16} color="#FFFFFF" />
                )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.option,
                localFilters.minDuration === 31 && styles.optionSelected,
              ]}
              onPress={() =>
                updateFilter(
                  'minDuration',
                  localFilters.minDuration === 31 ? undefined : 31
                )
              }
            >
              <Text
                style={[
                  styles.optionText,
                  localFilters.minDuration === 31 && styles.optionTextSelected,
                ]}
              >
                Long ({'>'}30 min)
              </Text>
              {localFilters.minDuration === 31 && (
                <Check size={16} color="#FFFFFF" />
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Readiness Filter */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Availability</Text>
          <TouchableOpacity
            style={[
              styles.option,
              localFilters.readyOnly === true && styles.optionSelected,
            ]}
            onPress={() =>
              updateFilter(
                'readyOnly',
                localFilters.readyOnly === true ? undefined : true
              )
            }
          >
            <Text
              style={[
                styles.optionText,
                localFilters.readyOnly === true && styles.optionTextSelected,
              ]}
            >
              Ready for Learning Only
            </Text>
            {localFilters.readyOnly === true && (
              <Check size={16} color="#FFFFFF" />
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.clearButton}
          onPress={handleClearFilters}
        >
          <Text style={styles.clearButtonText}>Clear All</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.applyButton}
          onPress={handleApplyFilters}
        >
          <Text style={styles.applyButtonText}>Apply Filters</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  optionGroup: {
    gap: 8,
  },
  option: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#FFFFFF',
  },
  optionSelected: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  optionText: {
    fontSize: 14,
    color: '#374151',
  },
  optionTextSelected: {
    color: '#FFFFFF',
    fontWeight: '500',
  },
  footer: {
    flexDirection: 'row',
    padding: 20,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  clearButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  clearButtonText: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  applyButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#3B82F6',
    alignItems: 'center',
  },
  applyButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
