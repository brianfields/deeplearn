import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import type { Unit } from '../models';

interface Props {
  unit: Unit;
  onPress: (u: Unit) => void;
  index?: number;
}

export function UnitCard({ unit, onPress, index }: Props) {
  return (
    <TouchableOpacity
      onPress={() => onPress(unit)}
      activeOpacity={0.85}
      testID={`unit-card-${index}`}
    >
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>{unit.title}</Text>
          <Text style={styles.badge}>{unit.difficultyLabel}</Text>
        </View>
        <Text style={styles.description} numberOfLines={2}>
          {unit.description || 'No description provided.'}
        </Text>
        <View style={styles.footer}>
          <Text style={styles.meta}>{unit.lessonCount} lessons</Text>
        </View>
      </View>
    </TouchableOpacity>
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
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  badge: {
    backgroundColor: '#E5E7EB',
    color: '#374151',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    fontSize: 12,
    overflow: 'hidden',
  },
  description: { color: '#4B5563', fontSize: 14, marginBottom: 8 },
  footer: { flexDirection: 'row', justifyContent: 'space-between' },
  meta: { color: '#6B7280', fontSize: 12 },
});
