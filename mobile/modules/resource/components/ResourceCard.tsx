import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type GestureResponderEvent,
} from 'react-native';
import type { ResourceSummary } from '../models';

interface Props {
  readonly resource: ResourceSummary;
  readonly onPress?: (event: GestureResponderEvent) => void;
}

function formatFileSize(size: number | null): string {
  if (!size || size <= 0) {
    return 'Unknown size';
  }
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = size;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function formatDate(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleDateString();
  } catch {
    return timestamp;
  }
}

export function ResourceCard({ resource, onPress }: Props): React.ReactElement {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
    >
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={1}>
          {resource.filename ?? resource.sourceUrl ?? 'Untitled resource'}
        </Text>
        <Text style={styles.meta}>{resource.resourceType}</Text>
      </View>
      <Text style={styles.preview} numberOfLines={2}>
        {resource.previewText || 'No preview available yet.'}
      </Text>
      <View style={styles.footer}>
        <Text style={styles.meta}>{formatFileSize(resource.fileSize)}</Text>
        <Text style={styles.meta}>Added {formatDate(resource.createdAt)}</Text>
      </View>
    </Pressable>
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
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardPressed: {
    opacity: 0.85,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  title: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    marginRight: 8,
  },
  preview: {
    color: '#444',
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  meta: {
    fontSize: 12,
    color: '#666',
  },
});
