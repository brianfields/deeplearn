/**
 * Results Screen - Simplified version for modular architecture
 *
 * Shows learning session results with score, stats, and navigation options.
 * This is a placeholder implementation compatible with the new modular structure.
 */

import React from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';
import { CheckCircle } from 'lucide-react-native';

// Components
import { Button, Card } from '../../ui_system/public';

// Theme & Types
import { uiSystemProvider } from '../../ui_system/public';
import type { LearningStackParamList } from '../../../types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<LearningStackParamList, 'Results'>;

export default function ResultsScreen({ navigation, route }: Props) {
  const { results } = route.params;

  // Get theme from ui_system
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const { colors, spacing, typography } = theme;

  // Calculate performance metrics (SessionResults shape)
  const scorePercentage = Math.max(0, Math.min(100, results.scorePercentage));
  const timeInMinutes = Math.round((results.totalTimeSeconds || 0) / 60);
  const completedSteps = results.completedComponents;

  const handleContinue = () => {
    navigation.popToTop();
  };

  const handleRetry = () => {
    navigation.goBack();
  };

  // Create styles with theme variables
  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    content: {
      flex: 1,
      padding: spacing.lg,
    },
    header: {
      alignItems: 'center',
      marginBottom: spacing.xl,
    },
    iconContainer: {
      width: 80,
      height: 80,
      borderRadius: 40,
      backgroundColor: colors.success,
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: spacing.md,
    },
    title: {
      fontSize: typography.heading2.fontSize,
      lineHeight: typography.heading2.lineHeight,
      color: colors.text,
      textAlign: 'center',
      marginBottom: spacing.sm,
      fontWeight: 'bold',
    },
    scoreContainer: {
      alignItems: 'center',
      marginBottom: spacing.xl,
    },
    scoreText: {
      ...typography.heading1,
      color: colors.primary,
      fontSize: 48,
      fontWeight: 'bold',
    },
    scoreLabel: {
      fontSize: typography.body.fontSize,
      lineHeight: typography.body.lineHeight,
      color: colors.textSecondary,
    },
    statsContainer: {
      marginBottom: spacing.xl,
    },
    statRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: spacing.md,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    statLabel: {
      fontSize: typography.body.fontSize,
      lineHeight: typography.body.lineHeight,
      color: colors.text,
    },
    statValue: {
      fontSize: typography.body.fontSize,
      lineHeight: typography.body.lineHeight,
      color: colors.primary,
      fontWeight: '600',
    },
    actionsContainer: {
      gap: spacing.md,
    },
    button: {
      marginBottom: spacing.sm,
    },
  });

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.iconContainer}>
            <CheckCircle size={40} color={colors.surface} />
          </View>
          <Text style={styles.title}>Session Complete!</Text>
        </View>

        {/* Score */}
        <Card style={styles.scoreContainer}>
          <Text style={styles.scoreText}>{Math.round(scorePercentage)}%</Text>
          <Text style={styles.scoreLabel}>Final Score</Text>
        </Card>

        {/* Stats */}
        <Card style={styles.statsContainer}>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Time Spent</Text>
            <Text style={styles.statValue}>{timeInMinutes} min</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Steps Completed</Text>
            <Text style={styles.statValue}>{completedSteps}</Text>
          </View>
          <View style={styles.statRow}>
            <Text style={styles.statLabel}>Status</Text>
            <Text style={styles.statValue}>
              {results.completionPercentage === 100
                ? 'Completed'
                : 'In Progress'}
            </Text>
          </View>
        </Card>

        {/* Actions */}
        <View style={styles.actionsContainer}>
          <Button
            title="Continue Learning"
            onPress={handleContinue}
            variant="primary"
            size="large"
            style={styles.button}
          />

          {scorePercentage < 80 && (
            <Button
              title="Try Again"
              onPress={handleRetry}
              variant="outline"
              size="large"
              style={styles.button}
            />
          )}
        </View>
      </View>
    </SafeAreaView>
  );
}
