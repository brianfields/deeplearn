import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

import type { LearningStackParamList } from '../../../types';
import {
  Box,
  Button,
  Card,
  Progress,
  Text,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { useAuth } from '../../user/public';
import { useUnitLOProgress } from '../../learning_session/queries';
import type { LOProgressItem, LOStatus } from '../../learning_session/models';

type UnitLODetailRoute = RouteProp<LearningStackParamList, 'UnitLODetail'>;
type UnitLODetailNavigation = NativeStackNavigationProp<
  LearningStackParamList,
  'UnitLODetail'
>;

interface CompactStatusMeta {
  readonly icon: string;
  readonly label: string;
  readonly color: string;
  readonly background: string;
}

export function UnitLODetailScreen(): React.ReactElement {
  const route = useRoute<UnitLODetailRoute>();
  const navigation = useNavigation<UnitLODetailNavigation>();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const { user } = useAuth();
  const unitId = route.params?.unitId ?? '';
  const unitTitle = route.params?.unitTitle ?? '';
  const userKey = user?.id ? String(user.id) : 'anonymous';

  const { data: progress, isLoading, isFetching } = useUnitLOProgress(
    userKey,
    unitId,
    {
      enabled: Boolean(unitId && userKey),
      staleTime: 60 * 1000,
    }
  );

  const statusMeta = useMemo(() => createStatusMeta(theme.colors), [theme.colors]);
  const items = progress?.items ?? [];

  const handleHeaderBack = () => {
    haptics.trigger('light');
    navigation.goBack();
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Box p="lg" pb="sm">
          <TouchableOpacity
            onPress={handleHeaderBack}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            style={{ paddingVertical: 6, paddingRight: 12 }}
          >
            <Text variant="body" color={theme.colors.primary}>
              {'‹ Back'}
            </Text>
          </TouchableOpacity>
          <Text variant="h1" style={{ marginTop: 8, fontWeight: 'normal' }}>
            {unitTitle || 'Learning Objectives'}
          </Text>
        </Box>

        {(isLoading || isFetching) && items.length === 0 ? (
          <Box px="lg" mt="lg">
            <Card variant="outlined" style={{ margin: 0 }}>
              <View style={styles.loadingRow}>
                <ActivityIndicator color={theme.colors.primary} />
                <Text
                  variant="body"
                  style={{ marginLeft: 12, color: theme.colors.textSecondary }}
                >
                  Loading progress…
                </Text>
              </View>
            </Card>
          </Box>
        ) : null}

        {items.length === 0 && !(isLoading || isFetching) ? (
          <Box px="lg" mt="lg">
            <Card variant="outlined" style={{ margin: 0 }}>
              <Text variant="body" color={theme.colors.textSecondary}>
                No learning objective progress is available yet. Complete lesson
                exercises to start tracking your mastery.
              </Text>
            </Card>
          </Box>
        ) : null}

        {items.map((item: LOProgressItem) => {
          const meta = statusMeta[item.status];
          const progressPercent =
            item.exercisesTotal > 0
              ? (item.exercisesCorrect / item.exercisesTotal) * 100
              : 0;

          return (
            <Box key={item.loId} px="lg" mt="md" testID={`unit-lo-detail-${item.loId}`}>
              <Card variant="outlined" style={{ margin: 0 }}>
                <View style={styles.itemHeader}>
                  <View
                    style={[
                      styles.statusIcon,
                      { backgroundColor: meta.background },
                    ]}
                  >
                    <Text style={[styles.statusIconText, { color: meta.color }]}> 
                      {meta.icon}
                    </Text>
                  </View>
                  <View style={styles.headerText}>
                    <Text style={[styles.itemTitle, { color: theme.colors.text }]}>
                      {item.title}
                    </Text>
                    <Text
                      style={[
                        styles.itemDescription,
                        { color: theme.colors.textSecondary },
                      ]}
                    >
                      {item.description}
                    </Text>
                  </View>
                </View>
                <View style={styles.progressSection}>
                  <View style={styles.progressLabels}>
                    <Text style={[styles.statusLabel, { color: meta.color }]}>
                      {meta.label}
                    </Text>
                    <Text
                      style={{ color: theme.colors.textSecondary, marginTop: 2 }}
                    >
                      {`${item.exercisesCorrect}/${item.exercisesTotal} correct`}
                    </Text>
                  </View>
                  <Progress
                    progress={progressPercent}
                    animated
                    size="medium"
                    color={meta.color}
                    backgroundColor={theme.colors.border}
                  />
                </View>
              </Card>
            </Box>
          );
        })}

        <Box px="lg" mt="xl" mb="xl">
          <Button
            title="Back to Unit"
            variant="secondary"
            onPress={() => navigation.goBack()}
          />
        </Box>
      </ScrollView>
    </SafeAreaView>
  );
}

function createStatusMeta(colors: any): Record<LOStatus, CompactStatusMeta> {
  return {
    completed: {
      icon: '✓',
      label: 'Mastered',
      color: colors.success,
      background: `${colors.success}1A`,
    },
    partial: {
      icon: '◐',
      label: 'In Progress',
      color: colors.warning,
      background: `${colors.warning}1A`,
    },
    not_started: {
      icon: '○',
      label: 'Not Started',
      color: colors.textSecondary,
      background: colors.border,
    },
  };
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollView: { flex: 1 },
  scrollContent: { paddingBottom: 48 },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  statusIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  statusIconText: {
    fontSize: 22,
    fontWeight: '600',
  },
  headerText: { flex: 1 },
  itemTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  itemDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  progressSection: {
    marginTop: 16,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 14,
    fontWeight: '600',
  },
});

export default UnitLODetailScreen;
