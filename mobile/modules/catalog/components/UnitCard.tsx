import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import type { Unit } from '../models';
import { UnitProgressIndicator } from './UnitProgressIndicator';

interface Props {
  unit: Unit;
  onPress: (u: Unit) => void;
  onRetry?: (unitId: string) => void;
  onDismiss?: (unitId: string) => void;
  index?: number;
}

export function UnitCard({ unit, onPress, onRetry, onDismiss, index }: Props) {
  const handlePress = () => {
    // Only allow interaction if unit is completed
    if (unit.isInteractive) {
      onPress(unit);
    }
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry(unit.id);
    }
  };

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss(unit.id);
    }
  };

  const showFailedActions = unit.status === 'failed' && (onRetry || onDismiss);

  return (
    <TouchableOpacity
      onPress={handlePress}
      activeOpacity={unit.isInteractive ? 0.85 : 1.0}
      disabled={!unit.isInteractive}
      testID={`unit-card-${index}`}
    >
      <View
        style={[
          styles.card,
          !unit.isInteractive && styles.cardDisabled,
          unit.status === 'failed' && styles.cardFailed,
        ]}
      >
        <View style={styles.header}>
          <Text
            style={[
              styles.title,
              !unit.isInteractive && styles.titleDisabled,
              unit.status === 'failed' && styles.titleFailed,
            ]}
          >
            {unit.title}
          </Text>
          <Text style={styles.badge}>{unit.difficultyLabel}</Text>
        </View>

        <Text
          style={[
            styles.description,
            !unit.isInteractive && styles.descriptionDisabled,
          ]}
          numberOfLines={2}
        >
          {unit.description || unit.progressMessage}
        </Text>

        {/* Status indicator for non-completed units */}
        {unit.status !== 'completed' && (
          <View style={styles.statusContainer}>
            <UnitProgressIndicator
              status={unit.status}
              progress={unit.creationProgress}
              errorMessage={unit.errorMessage}
            />
          </View>
        )}

        {/* Failed unit actions */}
        {showFailedActions && (
          <View style={styles.actionContainer}>
            {onRetry && (
              <TouchableOpacity
                style={[styles.actionButton, styles.retryButton]}
                onPress={handleRetry}
                testID={`retry-button-${index}`}
              >
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            )}
            {onDismiss && (
              <TouchableOpacity
                style={[styles.actionButton, styles.dismissButton]}
                onPress={handleDismiss}
                testID={`dismiss-button-${index}`}
              >
                <Text style={styles.dismissButtonText}>Dismiss</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        <View style={styles.footer}>
          <Text
            style={[styles.meta, !unit.isInteractive && styles.metaDisabled]}
          >
            {unit.lessonCount} lessons
          </Text>
          {typeof unit.targetLessonCount === 'number' && (
            <Text
              style={[styles.meta, !unit.isInteractive && styles.metaDisabled]}
            >
              Target: {unit.targetLessonCount}
            </Text>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardDisabled: {
    backgroundColor: '#F8F9FA',
    shadowOpacity: 0.02,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  titleDisabled: {
    color: '#8E8E93',
  },
  badge: {
    backgroundColor: '#E5E7EB',
    color: '#374151',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    fontSize: 12,
    overflow: 'hidden',
  },
  description: {
    color: '#4B5563',
    fontSize: 14,
    marginBottom: 8,
  },
  descriptionDisabled: {
    color: '#8E8E93',
  },
  statusContainer: {
    marginBottom: 8,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  meta: {
    color: '#6B7280',
    fontSize: 12,
  },
  metaDisabled: {
    color: '#C7C7CC',
  },
  cardFailed: {
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
  },
  titleFailed: {
    color: '#DC2626',
  },
  actionContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    marginBottom: 4,
    gap: 8,
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    minWidth: 64,
    alignItems: 'center',
  },
  retryButton: {
    backgroundColor: '#3B82F6',
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  dismissButton: {
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  dismissButtonText: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
  },
});
