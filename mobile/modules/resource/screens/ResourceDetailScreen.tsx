import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { ResourceStackParamList } from '../nav';
import { useResourceDetail } from '../queries';

type ScreenProps = NativeStackScreenProps<
  ResourceStackParamList,
  'ResourceDetail'
>;

function renderMetadata(metadata: Record<string, unknown>): string {
  try {
    return JSON.stringify(metadata, null, 2);
  } catch {
    return 'Metadata unavailable';
  }
}

export function ResourceDetailScreen({
  route,
}: ScreenProps): React.ReactElement {
  const { resourceId } = route.params;
  const detailQuery = useResourceDetail(resourceId);

  const metadataText = useMemo(() => {
    if (!detailQuery.data) {
      return 'Loading metadata…';
    }
    return renderMetadata(detailQuery.data.extractionMetadata);
  }, [detailQuery.data]);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {detailQuery.isLoading ? (
          <View style={styles.loader}>
            <ActivityIndicator />
            <Text style={styles.helper}>Fetching resource…</Text>
          </View>
        ) : detailQuery.data ? (
          <>
            <Text style={styles.title}>
              {detailQuery.data.filename ??
                detailQuery.data.sourceUrl ??
                'Untitled resource'}
            </Text>
            <Text style={styles.meta}>
              Type: {detailQuery.data.resourceType} • Uploaded{' '}
              {detailQuery.data.createdAt}
            </Text>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Extracted content</Text>
              <Text style={styles.bodyText}>
                {detailQuery.data.extractedText ||
                  'No extracted text available yet.'}
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Extraction metadata</Text>
              <View style={styles.metadataBox}>
                <Text style={styles.metadataText}>{metadataText}</Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Linked units</Text>
              <Text style={styles.helper}>
                Linked units will appear here once unit integration is complete.
              </Text>
            </View>
          </>
        ) : (
          <View style={styles.loader}>
            <Text style={styles.helper}>Resource not found.</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    padding: 20,
  },
  loader: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  helper: {
    color: '#4b5563',
    marginTop: 8,
    textAlign: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  meta: {
    color: '#4b5563',
    marginBottom: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  bodyText: {
    color: '#1f2937',
    lineHeight: 20,
  },
  metadataBox: {
    backgroundColor: '#fff',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: 12,
  },
  metadataText: {
    fontSize: 12,
    color: '#111827',
  },
});
