import React from 'react';
import { StyleSheet, View } from 'react-native';
import type { UnitProgress } from '../../content/public';
import { Progress, uiSystemProvider } from '../../ui_system/public';

export function UnitProgressView({ progress }: { progress: UnitProgress }) {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const pct = Math.max(
    0,
    Math.min(100, (progress.completedLessons / progress.totalLessons) * 100)
  );

  return (
    <View style={styles.container}>
      <Progress
        progress={pct}
        showLabel
        label={`${progress.completedLessons}/${progress.totalLessons} lessons`}
        color={theme.colors.primary}
        backgroundColor={theme.colors.border}
        animated
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginVertical: 8 },
});
