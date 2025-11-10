import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  Modal,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { uiSystemProvider } from '../../ui_system/public';
import { reducedMotion } from '../../ui_system/utils/motion';
import { ConversationHeader } from '../../learning_conversations/components/ConversationHeader';
import { Box, Card, Progress, Text } from '../../ui_system/public';
import type { LOProgressItem, LOStatus } from '../../learning_session/models';
import { layoutStyles } from '../../ui_system/styles/layout';

interface Props {
  readonly visible: boolean;
  readonly onClose: () => void;
  readonly unitTitle: string;
  readonly progressItems: LOProgressItem[];
  readonly isLoading?: boolean;
  readonly isFetching?: boolean;
}

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

interface CompactStatusMeta {
  readonly icon: string;
  readonly label: string;
  readonly color: string;
  readonly background: string;
}

/**
 * UnitProgressModal
 *
 * Displays an overlay modal for viewing detailed learning objective progress.
 *
 * Animation & Accessibility:
 * - Respects reduced motion setting (no animation when enabled)
 * - Uses appropriate animation timing
 * - On Android: hardware back button handled via onRequestClose
 */
export function UnitProgressModal({
  visible,
  onClose,
  unitTitle,
  progressItems,
  isLoading = false,
  isFetching = false,
}: Props): React.ReactElement {
  const statusMeta = useMemo(() => createStatusMeta(theme.colors), []);
  const items = progressItems ?? [];

  // Use no animation if reduced motion is enabled
  const animationType = reducedMotion.enabled ? 'none' : 'slide';

  return (
    <Modal
      animationType={animationType}
      visible={visible}
      presentationStyle="pageSheet"
      onRequestClose={onClose}
      testID="unit-progress-modal"
    >
      <SafeAreaView style={styles.container}>
        <ConversationHeader
          title={unitTitle || 'Learning Objectives'}
          onClose={onClose}
        />

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {(isLoading || isFetching) && items.length === 0 ? (
            <Box px="lg" mt="lg">
              <Card variant="outlined" style={localStyles.noMargin}>
                <View style={styles.loadingRow}>
                  <ActivityIndicator color={theme.colors.primary} />
                  <Text
                    variant="body"
                    style={[
                      layoutStyles.selfStart,
                      localStyles.marginLeft12,
                      { color: theme.colors.textSecondary },
                    ]}
                  >
                    Loading progress…
                  </Text>
                </View>
              </Card>
            </Box>
          ) : null}

          {items.length === 0 && !(isLoading || isFetching) ? (
            <Box px="lg" mt="lg">
              <Card variant="outlined" style={localStyles.noMargin}>
                <Text variant="body" color={theme.colors.textSecondary}>
                  No learning objective progress is available yet. Complete
                  lesson exercises to start tracking your mastery.
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
              <Box
                key={item.loId}
                px="lg"
                mt="md"
                testID={`unit-lo-detail-${item.loId}`}
              >
                <Card variant="outlined" style={localStyles.noMargin}>
                  <View style={styles.itemHeader}>
                    <View
                      style={[
                        styles.statusIcon,
                        { backgroundColor: meta.background },
                      ]}
                    >
                      <Text
                        style={[styles.statusIconText, { color: meta.color }]}
                      >
                        {meta.icon}
                      </Text>
                    </View>
                    <View style={styles.headerText}>
                      <Text
                        style={[styles.itemTitle, { color: theme.colors.text }]}
                      >
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
                        style={[
                          styles.statusLabel,
                          { color: theme.colors.textSecondary },
                          localStyles.marginTop2,
                        ]}
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
        </ScrollView>
      </SafeAreaView>
    </Modal>
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
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 48,
  },
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

const localStyles = StyleSheet.create({
  noMargin: {
    margin: 0,
  },
  marginTop2: {
    marginTop: 2,
  },
  marginLeft12: {
    marginLeft: 12,
  },
});
