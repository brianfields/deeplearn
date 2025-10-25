/**
 * Unit Progress Indicator Component
 *
 * Shows the current status of unit creation with visual indicators.
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { uiSystemProvider } from '../../ui_system/public';
import type { UnitStatus, UnitCreationProgress } from '../../content/public';

interface UnitProgressIndicatorProps {
  status: UnitStatus;
  progress?: UnitCreationProgress | null;
  errorMessage?: string | null;
  size?: 'small' | 'large';
  isStale?: boolean;
}

export function UnitProgressIndicator({
  status,
  progress,
  errorMessage,
  size = 'small',
  isStale = false,
}: UnitProgressIndicatorProps) {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const styles = getStyles(size, theme);

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
              color={theme.colors.primary}
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
        if (isStale) {
          return 'Creation is taking longer than expected. Please refresh to check status.';
        }
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
        return theme.colors.textSecondary;
      case 'in_progress':
        return isStale ? theme.colors.warning : theme.colors.primary;
      case 'completed':
        return theme.colors.success;
      case 'failed':
        return theme.colors.error;
      default:
        return theme.colors.textSecondary;
    }
  };

  if (size === 'large') {
    return (
      <View style={styles.containerLarge}>
        {renderStatusIcon()}
        <View style={styles.textContainer}>
          <Text style={[styles.statusLabel, { color: getStatusColor() }]}>
            {getStatusLabel(status, isStale)}
          </Text>
          <Text style={styles.statusMessage}>{getStatusMessage()}</Text>
          {status === 'in_progress' && progress?.stage && !isStale && (
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
        {getStatusLabel(status, isStale)}
      </Text>
    </View>
  );
}

function getStatusLabel(status: UnitStatus, isStale?: boolean): string {
  if (status === 'in_progress' && isStale) {
    return 'Taking longer than expected...';
  }
  const statusMap: Record<UnitStatus, string> = {
    draft: 'Draft',
    in_progress: 'Creating...',
    completed: 'Ready',
    failed: 'Failed',
  };
  return statusMap[status] ?? 'Unknown';
}

function getStyles(size: 'small' | 'large', theme: any) {
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
      backgroundColor: theme.colors.surface,
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
      backgroundColor: theme.colors.border,
    },
    progressIcon: {
      backgroundColor: theme.colors.border,
    },
    completedIcon: {
      backgroundColor: `${theme.colors.success}1A`,
    },
    failedIcon: {
      backgroundColor: `${theme.colors.error}1A`,
    },
    statusText: {
      fontSize: size === 'large' ? 18 : 12,
    },
    textContainer: {
      flex: 1,
    },
    statusLabel: {
      fontSize: size === 'large' ? 16 : 14,
      fontWeight: '400',
      marginBottom: size === 'large' ? 4 : 0,
    },
    statusMessage: {
      fontSize: 14,
      color: theme.colors.textSecondary,
      lineHeight: 18,
    },
    stageText: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginTop: 4,
      fontStyle: 'italic',
    },
  });
}
