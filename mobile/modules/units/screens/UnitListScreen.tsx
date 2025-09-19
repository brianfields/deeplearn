import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  FlatList,
  TextInput,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Search } from 'lucide-react-native';

import { useUnits } from '../queries';
import { UnitCard } from '../components/UnitCard';
import type { Unit } from '../models';
import type { LearningStackParamList } from '../../../types';

export function UnitListScreen() {
  const navigation =
    useNavigation<NativeStackNavigationProp<LearningStackParamList>>();
  const { data: units = [], isLoading } = useUnits();
  const [query, setQuery] = useState('');

  const filtered = units.filter(
    u =>
      !query.trim() ||
      u.title.toLowerCase().includes(query.trim().toLowerCase())
  );

  const onPress = useCallback(
    (_: Unit) => {
      navigation.navigate('LessonList');
      // In future: navigate to a UnitDetail screen
    },
    [navigation]
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Units</Text>
        <Text style={styles.subtitle}>{units.length} available</Text>
      </View>
      <View style={styles.searchRow}>
        <Search size={20} color="#9CA3AF" style={styles.icon} />
        <TextInput
          style={styles.search}
          placeholder="Search units..."
          value={query}
          onChangeText={setQuery}
          placeholderTextColor="#9CA3AF"
        />
      </View>
      <FlatList
        data={filtered}
        keyExtractor={i => i.id}
        renderItem={({ item }) => <UnitCard unit={item} onPress={onPress} />}
        contentContainerStyle={styles.list}
        refreshing={isLoading}
        onRefresh={() => {}}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { padding: 20, paddingBottom: 12 },
  title: { fontSize: 28, fontWeight: '700', color: '#111827' },
  subtitle: { fontSize: 14, color: '#6B7280', marginTop: 4 },
  searchRow: {
    marginHorizontal: 20,
    marginBottom: 12,
    borderRadius: 12,
    backgroundColor: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  search: { flex: 1, fontSize: 16, color: '#111827' },
  icon: { marginRight: 8 },
  list: { padding: 20, paddingTop: 0 },
});
