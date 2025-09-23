/**
 * SearchFilters component for lesson catalog.
 *
 * Provides UI controls for filtering and sorting lessons.
 */

import React, { useState } from 'react';
import { View, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { X, Check } from 'lucide-react-native';

import { LessonFilters } from '../models';
import {
  Text,
  Button,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';

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
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { trigger } = useHaptics();

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    trigger('medium');
    onClose?.();
  };

  const handleClearFilters = () => {
    const clearedFilters: LessonFilters = {};
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
    trigger('light');
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
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surface,
          borderTopLeftRadius: 20,
          borderTopRightRadius: 20,
        },
      ]}
    >
      {/* Grabber bar for sheet affordance */}
      <View
        style={{
          alignItems: 'center',
          paddingTop: ui.getSpacing('sm'),
        }}
      >
        <View
          style={{
            width: 36,
            height: 4,
            borderRadius: 2,
            backgroundColor: theme.colors.textSecondary,
            opacity: 0.2,
          }}
        />
      </View>

      <View
        style={[
          styles.header,
          {
            padding: ui.getSpacing('lg'),
            borderBottomWidth: StyleSheet.hairlineWidth,
            borderBottomColor: theme.colors.border,
          },
        ]}
      >
        <Text variant="h2">Filter Lessons</Text>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        style={[styles.content, { padding: ui.getSpacing('lg') }]}
        contentContainerStyle={{ paddingBottom: ui.getSpacing('lg') }}
      >
        {/* User Level Filter */}
        <View style={[styles.section, { marginBottom: ui.getSpacing('lg') }]}>
          <Text variant="title" weight="700">
            Difficulty Level
          </Text>
          <View style={[styles.optionGroup, { gap: ui.getSpacing('xs') }]}>
            {(['beginner', 'intermediate', 'advanced'] as const).map(level => (
              <TouchableOpacity
                key={level}
                style={[
                  styles.option,
                  {
                    borderRadius: 12,
                    borderWidth: StyleSheet.hairlineWidth,
                    borderColor: theme.colors.border,
                    backgroundColor: theme.colors.surface,
                    minHeight: 44,
                    padding: ui.getSpacing('sm'),
                  },
                  localFilters.userLevel === level && {
                    backgroundColor: theme.colors.primary,
                    borderColor: theme.colors.primary,
                  },
                ]}
                onPress={() => {
                  trigger('medium');
                  updateFilter(
                    'userLevel',
                    localFilters.userLevel === level ? undefined : level
                  );
                }}
              >
                <Text
                  style={{ flex: 1 }}
                  variant="body"
                  color={
                    localFilters.userLevel === level
                      ? theme.colors.surface
                      : theme.colors.text
                  }
                  weight={localFilters.userLevel === level ? '600' : undefined}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </Text>
                {localFilters.userLevel === level && (
                  <Check size={16} color={theme.colors.surface} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Duration Filter */}
        <View style={[styles.section, { marginBottom: ui.getSpacing('lg') }]}>
          <Text variant="title" weight="700">
            Duration
          </Text>
          <View style={[styles.optionGroup, { gap: ui.getSpacing('xs') }]}>
            <TouchableOpacity
              style={[
                styles.option,
                {
                  borderRadius: 12,
                  borderWidth: StyleSheet.hairlineWidth,
                  borderColor: theme.colors.border,
                  backgroundColor: theme.colors.surface,
                  minHeight: 44,
                  padding: ui.getSpacing('sm'),
                },
                localFilters.maxDuration === 15 && {
                  backgroundColor: theme.colors.primary,
                  borderColor: theme.colors.primary,
                },
              ]}
              onPress={() => {
                trigger('medium');
                updateFilter(
                  'maxDuration',
                  localFilters.maxDuration === 15 ? undefined : 15
                );
              }}
            >
              <Text
                variant="body"
                color={
                  localFilters.maxDuration === 15
                    ? theme.colors.surface
                    : theme.colors.text
                }
                weight={localFilters.maxDuration === 15 ? '600' : undefined}
              >
                Quick (≤15 min)
              </Text>
              {localFilters.maxDuration === 15 && (
                <Check size={16} color={theme.colors.surface} />
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.option,
                {
                  borderRadius: 12,
                  borderWidth: StyleSheet.hairlineWidth,
                  borderColor: theme.colors.border,
                  backgroundColor: theme.colors.surface,
                  minHeight: 44,
                  padding: ui.getSpacing('sm'),
                },
                localFilters.minDuration === 16 &&
                  localFilters.maxDuration === 30 && {
                    backgroundColor: theme.colors.primary,
                    borderColor: theme.colors.primary,
                  },
              ]}
              onPress={() => {
                trigger('medium');
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
                variant="body"
                color={
                  localFilters.minDuration === 16 &&
                  localFilters.maxDuration === 30
                    ? theme.colors.surface
                    : theme.colors.text
                }
                weight={
                  localFilters.minDuration === 16 &&
                  localFilters.maxDuration === 30
                    ? '600'
                    : undefined
                }
              >
                Medium (16-30 min)
              </Text>
              {localFilters.minDuration === 16 &&
                localFilters.maxDuration === 30 && (
                  <Check size={16} color={theme.colors.surface} />
                )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.option,
                {
                  borderRadius: 12,
                  borderWidth: StyleSheet.hairlineWidth,
                  borderColor: theme.colors.border,
                  backgroundColor: theme.colors.surface,
                  minHeight: 44,
                  padding: ui.getSpacing('sm'),
                },
                localFilters.minDuration === 31 && {
                  backgroundColor: theme.colors.primary,
                  borderColor: theme.colors.primary,
                },
              ]}
              onPress={() => {
                trigger('medium');
                updateFilter(
                  'minDuration',
                  localFilters.minDuration === 31 ? undefined : 31
                );
              }}
            >
              <Text
                variant="body"
                color={
                  localFilters.minDuration === 31
                    ? theme.colors.surface
                    : theme.colors.text
                }
                weight={localFilters.minDuration === 31 ? '600' : undefined}
              >
                Long ({'>'}30 min)
              </Text>
              {localFilters.minDuration === 31 && (
                <Check size={16} color={theme.colors.surface} />
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Readiness Filter */}
        <View style={[styles.section, { marginBottom: ui.getSpacing('lg') }]}>
          <Text variant="title" weight="700">
            Availability
          </Text>
          <TouchableOpacity
            style={[
              styles.option,
              {
                borderRadius: 12,
                borderWidth: StyleSheet.hairlineWidth,
                borderColor: theme.colors.border,
                backgroundColor: theme.colors.surface,
                minHeight: 44,
                padding: ui.getSpacing('sm'),
              },
              localFilters.readyOnly === true && {
                backgroundColor: theme.colors.primary,
                borderColor: theme.colors.primary,
              },
            ]}
            onPress={() => {
              trigger('medium');
              updateFilter(
                'readyOnly',
                localFilters.readyOnly === true ? undefined : true
              );
            }}
          >
            <Text
              variant="body"
              color={
                localFilters.readyOnly === true
                  ? theme.colors.surface
                  : theme.colors.text
              }
              weight={localFilters.readyOnly === true ? '600' : undefined}
            >
              Ready for Learning Only
            </Text>
            {localFilters.readyOnly === true && (
              <Check size={16} color={theme.colors.surface} />
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>

      <View
        style={{
          flexDirection: 'row',
          padding: ui.getSpacing('lg'),
          gap: ui.getSpacing('sm'),
          borderTopWidth: StyleSheet.hairlineWidth,
          borderTopColor: theme.colors.border,
        }}
      >
        <Button
          title="Clear All"
          variant="secondary"
          size="medium"
          onPress={handleClearFilters}
          fullWidth
        />
        <Button
          title="Apply Filters"
          variant="primary"
          size="medium"
          onPress={handleApplyFilters}
          fullWidth
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    maxHeight: '80%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
  },
  section: {
    // margin provided dynamically
  },
  optionGroup: {
    // gap provided dynamically
  },
  option: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
});
