import React, { useMemo } from 'react';
import type { JSX } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import {
  CheckCircle,
  AlertTriangle,
  Circle,
  Sparkles,
} from 'lucide-react-native';
import { Card, uiSystemProvider } from '../../ui_system/public';
import type { LOProgressItem as LOProgressRecord, LOStatus } from '../models';

type Props = {
  readonly item: LOProgressRecord;
  readonly testID?: string;
};

type StatusMeta = {
  readonly icon: typeof CheckCircle;
  readonly label: string;
};

const STATUS_META: Record<LOStatus, StatusMeta> = {
  completed: { icon: CheckCircle, label: 'Mastered' },
  partial: { icon: AlertTriangle, label: 'In Progress' },
  not_started: { icon: Circle, label: 'Not Started' },
};

export function LOProgressItem({ item, testID }: Props): JSX.Element {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { icon: StatusIcon, label } = STATUS_META[item.status];
  const statusColor = useMemo(() => {
    switch (item.status) {
      case 'completed':
        return theme.colors.success;
      case 'partial':
        return theme.colors.warning;
      default:
        return theme.colors.textSecondary;
    }
  }, [
    item.status,
    theme.colors.success,
    theme.colors.warning,
    theme.colors.textSecondary,
  ]);

  const exercisesAttempted = item.exercisesAttempted ?? 0;
  const progressLabel = `${item.exercisesCorrect}/${item.exercisesTotal} correct`;
  const attemptedLabel = `${exercisesAttempted} attempted`;

  return (
    <Card
      variant="outlined"
      style={[styles.card, { borderColor: statusColor }]}
      testID={testID ?? `lo-progress-item-${item.loId}`}
    >
      <View style={styles.row}>
        <View
          style={[
            styles.iconContainer,
            { backgroundColor: `${statusColor}1A` },
          ]}
        >
          <StatusIcon size={24} color={statusColor} />
        </View>
        <View style={styles.content}>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            {item.title}
          </Text>
          <Text
            style={[styles.description, { color: theme.colors.textSecondary }]}
            numberOfLines={2}
            ellipsizeMode="tail"
          >
            {item.description}
          </Text>
          <View style={styles.metaRow}>
            <Text
              style={[styles.status, { color: statusColor }]}
              accessibilityLabel={`Status ${label}`}
            >
              {label}
            </Text>
            <Text
              style={[
                styles.progressLabel,
                { color: theme.colors.textSecondary },
              ]}
            >
              {progressLabel}
            </Text>
            <Text
              style={[
                styles.progressLabel,
                { color: theme.colors.textSecondary },
              ]}
            >
              {attemptedLabel}
            </Text>
          </View>
        </View>
        {item.newlyCompletedInSession ? (
          <View
            style={[styles.badge, { backgroundColor: theme.colors.accent }]}
            testID={`${testID ?? `lo-progress-item-${item.loId}`}-new-badge`}
          >
            <Sparkles size={14} color={theme.colors.surface} />
            <Text style={[styles.badgeText, { color: theme.colors.surface }]}>
              NEW
            </Text>
          </View>
        ) : null}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 2,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    columnGap: 12,
    rowGap: 4,
    marginTop: 8,
  },
  status: {
    fontSize: 14,
    fontWeight: '600',
  },
  progressLabel: {
    fontSize: 14,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    marginLeft: 12,
    gap: 4,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});

export default LOProgressItem;
