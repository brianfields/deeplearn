/**
 * Unit Progress Indicator Component
 *
 * Shows the current status of unit creation with visual indicators.
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import type { UnitStatus, UnitCreationProgress } from '../models';

interface UnitProgressIndicatorProps {
  status: UnitStatus;
  progress?: UnitCreationProgress | null;
  errorMessage?: string | null;
  size?: 'small' | 'large';
}

export function UnitProgressIndicator({
  status,
  progress,
  errorMessage,
  size = 'small',
}: UnitProgressIndicatorProps) {
  const styles = getStyles(size);

  const renderStatusIcon = () => {
    switch (status) {
      case 'draft':
        return (
          <View style={[styles.statusIcon, styles.draftIcon]}>
            <Text style={styles.statusText}>📝</Text>
          </View>
        );
      case 'in_progress':
        return (
          <View style={[styles.statusIcon, styles.progressIcon]}>
            <ActivityIndicator
              size={size === 'large' ? 'large' : 'small'}
              color="#007AFF"
            />
          </View>
        );
      case 'completed':
        return (
          <View style={[styles.statusIcon, styles.completedIcon]}>
            <Text style={styles.statusText}>✅</Text>
          </View>
        );
      case 'failed':
        return (
          <View style={[styles.statusIcon, styles.failedIcon]}>
            <Text style={styles.statusText}>❌</Text>
          </View>
        );
      default:
        return null;
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case 'draft':
        return 'Unit is being prepared';
      case 'in_progress':
        return progress?.message || 'Creating unit content...';
      case 'completed':
        return 'Ready to learn';
      case 'failed':
        return errorMessage || 'Creation failed';
      default:
        return 'Unknown status';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'draft':
        return '#8E8E93';
      case 'in_progress':
        return '#007AFF';
      case 'completed':
        return '#34C759';
      case 'failed':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

  if (size === 'large') {
    return (
      <View style={styles.containerLarge}>
        {renderStatusIcon()}
        <View style={styles.textContainer}>
          <Text style={[styles.statusLabel, { color: getStatusColor() }]}>
            {getStatusLabel(status)}
          </Text>
          <Text style={styles.statusMessage}>{getStatusMessage()}</Text>
          {status === 'in_progress' && progress?.stage && (
            <Text style={styles.stageText}>Stage: {progress.stage}</Text>
          )}
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {renderStatusIcon()}
      <Text style={[styles.statusLabel, { color: getStatusColor() }]}>
        {getStatusLabel(status)}
      </Text>
    </View>
  );
}

function getStatusLabel(status: UnitStatus): string {
  const statusMap: Record<UnitStatus, string> = {
    draft: 'Draft',
    in_progress: 'Creating...',
    completed: 'Ready',
    failed: 'Failed',
  };
  return statusMap[status] ?? 'Unknown';
}

function getStyles(size: 'small' | 'large') {
  return StyleSheet.create({
    container: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
    },
    containerLarge: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      gap: 12,
      padding: 12,
      backgroundColor: '#F2F2F7',
      borderRadius: 8,
    },
    statusIcon: {
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: size === 'large' ? 20 : 12,
      width: size === 'large' ? 40 : 24,
      height: size === 'large' ? 40 : 24,
    },
    draftIcon: {
      backgroundColor: '#E5E5EA',
    },
    progressIcon: {
      backgroundColor: '#E3F2FD',
    },
    completedIcon: {
      backgroundColor: '#E8F5E8',
    },
    failedIcon: {
      backgroundColor: '#FFEBEE',
    },
    statusText: {
      fontSize: size === 'large' ? 18 : 12,
    },
    textContainer: {
      flex: 1,
    },
    statusLabel: {
      fontSize: size === 'large' ? 16 : 14,
      fontWeight: '600',
      marginBottom: size === 'large' ? 4 : 0,
    },
    statusMessage: {
      fontSize: 14,
      color: '#8E8E93',
      lineHeight: 18,
    },
    stageText: {
      fontSize: 12,
      color: '#8E8E93',
      marginTop: 4,
      fontStyle: 'italic',
    },
  });
}
