import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useAuth } from '../../user/public';
import { ResourceCard } from '../components/ResourceCard';
import { useUserResources } from '../queries';
import type { ResourceStackParamList } from '../nav';

type ScreenProps = NativeStackScreenProps<
  ResourceStackParamList,
  'ResourceLibrary'
>;

export function ResourceLibraryScreen({
  navigation,
}: ScreenProps): React.ReactElement {
  const { user } = useAuth();
  const userId = user?.id ?? null;
  const [search, setSearch] = useState('');
  const resourcesQuery = useUserResources(userId, { enabled: !!userId });

  const filteredResources = useMemo(() => {
    const list = resourcesQuery.data ?? [];
    if (!search.trim()) {
      return list;
    }
    const normalized = search.trim().toLowerCase();
    return list.filter(resource => {
      const label =
        resource.filename ?? resource.sourceUrl ?? resource.resourceType;
      return label.toLowerCase().includes(normalized);
    });
  }, [resourcesQuery.data, search]);

  if (!userId) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.helperText}>Sign in to view your resource library.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Your resources</Text>
        <Pressable
          style={styles.addButton}
          onPress={() => navigation.navigate('AddResource')}
        >
          <Text style={styles.addButtonText}>Add resource</Text>
        </Pressable>
      </View>

      <TextInput
        placeholder="Search by name or URL"
        value={search}
        onChangeText={setSearch}
        style={styles.searchInput}
        autoCapitalize="none"
      />

      {resourcesQuery.isLoading ? (
        <View style={styles.loader}>
          <ActivityIndicator />
        </View>
      ) : (
        <FlatList
          data={filteredResources}
          keyExtractor={item => item.id}
          renderItem={({ item }) => (
            <ResourceCard
              resource={item}
              onPress={() => navigation.navigate('ResourceDetail', { resourceId: item.id })}
            />
          )}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={() => (
            <View style={styles.emptyState}>
              <Text style={styles.helperText}>
                No resources yet. Upload a file or paste a URL to get started.
              </Text>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f9fafb',
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
  },
  addButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 10,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  searchInput: {
    backgroundColor: '#fff',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: 12,
    marginBottom: 16,
  },
  loader: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listContent: {
    paddingBottom: 24,
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  helperText: {
    color: '#4b5563',
    textAlign: 'center',
  },
});
