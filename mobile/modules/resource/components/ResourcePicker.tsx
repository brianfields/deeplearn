import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { ResourceCard } from './ResourceCard';
import type { ResourceSummary } from '../models';

interface Props {
  readonly resources: ResourceSummary[];
  readonly onSelect: (resource: ResourceSummary) => void;
  readonly isLoading?: boolean;
  readonly sharedResourceIds?: Set<string>;
}

export function ResourcePicker({
  resources,
  onSelect,
  isLoading = false,
  sharedResourceIds = new Set(),
}: Props): React.ReactElement {
  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="small" />
        <Text style={styles.helper}>Loading your resources…</Text>
      </View>
    );
  }

  if (!resources.length) {
    return (
      <View style={styles.centered}>
        <Text style={styles.helper}>
          You have not uploaded any resources yet. Upload a file or paste a URL
          to see it here.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.listContent}>
      {resources.map(resource => (
        <ResourceCard
          key={resource.id}
          resource={resource}
          onPress={() => onSelect(resource)}
          isShared={sharedResourceIds.has(resource.id)}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  centered: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
  },
  helper: {
    color: '#555',
    textAlign: 'center',
    paddingHorizontal: 16,
    marginTop: 8,
  },
  listContent: {
    paddingBottom: 24,
  },
});
