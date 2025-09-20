import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { UnitProgress } from '../models';

export function UnitProgressView({ progress }: { progress: UnitProgress }) {
  const pct = progress.progressPercentage;
  return (
    <View style={styles.container}>
      <View style={styles.barBackground}>
        <View style={[styles.barFill, { width: `${pct}%` }]} />
      </View>
      <Text style={styles.label}>
        {progress.completedLessons}/{progress.totalLessons} lessons • {pct}%
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginVertical: 8 },
  barBackground: {
    height: 10,
    backgroundColor: '#E5E7EB',
    borderRadius: 6,
    overflow: 'hidden',
  },
  barFill: {
    height: 10,
    backgroundColor: '#3B82F6',
  },
  label: { marginTop: 6, color: '#374151', fontSize: 12, textAlign: 'right' },
});
