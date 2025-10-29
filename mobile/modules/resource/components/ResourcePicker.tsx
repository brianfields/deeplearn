import React from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { ResourceCard } from './ResourceCard';
import type { ResourceSummary } from '../models';

interface Props {
  readonly resources: ResourceSummary[];
  readonly onSelect: (resource: ResourceSummary) => void;
  readonly isLoading?: boolean;
}

export function ResourcePicker({
  resources,
  onSelect,
  isLoading = false,
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
    <FlatList
      data={resources}
      keyExtractor={item => item.id}
      renderItem={({ item }) => (
        <ResourceCard resource={item} onPress={() => onSelect(item)} />
      )}
      contentContainerStyle={styles.listContent}
    />
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
