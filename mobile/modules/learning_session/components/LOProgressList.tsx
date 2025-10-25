import React from 'react';
import type { JSX } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { uiSystemProvider, Card } from '../../ui_system/public';
import type { LOProgressItem as LOProgressRecord } from '../models';
import { LOProgressItem } from './LOProgressItem';

type Props = {
  readonly items: LOProgressRecord[];
  readonly isLoading?: boolean;
  readonly emptyMessage?: string;
  readonly testID?: string;
};

export function LOProgressList({
  items,
  isLoading = false,
  emptyMessage = 'Learning objectives for this unit will appear here once available.',
  testID = 'lo-progress-list',
}: Props): JSX.Element {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();

  if (isLoading && !items.length) {
    return (
      <Card style={styles.loadingCard} testID={`${testID}-loading`}>
        <ActivityIndicator color={theme.colors.primary} size="small" />
        <Text
          style={[styles.loadingText, { color: theme.colors.textSecondary }]}
        >
          Calculating progress…
        </Text>
      </Card>
    );
  }

  if (!items.length) {
    return (
      <Card style={styles.emptyCard} testID={`${testID}-empty`}>
        <Text style={[styles.emptyTitle, { color: theme.colors.text }]}>
          No learning objectives yet
        </Text>
        <Text
          style={[styles.emptyMessage, { color: theme.colors.textSecondary }]}
        >
          {emptyMessage}
        </Text>
      </Card>
    );
  }

  return (
    <View style={styles.container} testID={testID}>
      {items.map((item, index) => (
        <LOProgressItem
          key={item.loId}
          item={item}
          testID={`${testID}-item-${index}`}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  loadingCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  emptyCard: {
    alignItems: 'flex-start',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  emptyMessage: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default LOProgressList;
