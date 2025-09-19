import React from 'react';
import { SafeAreaView, Text, StyleSheet } from 'react-native';

export function UnitProgressScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.text}>Unit Progress</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  text: { fontSize: 18 },
});
