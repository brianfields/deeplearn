import React from 'react';
import { StyleSheet, View } from 'react-native';
import type { LOStatus } from '../../learning_session/models';
import type { UnitProgress } from '../../content/public';
import {
  Progress,
  Text as UiText,
  uiSystemProvider,
} from '../../ui_system/public';

interface ObjectiveStatusMeta {
  readonly icon: string;
  readonly label: string;
  readonly color: string;
  readonly background: string;
}

export interface UnitObjectiveSummary {
  readonly id: string;
  readonly title: string;
  readonly status: LOStatus;
  readonly progress?: {
    readonly exercisesCorrect: number;
    readonly exercisesTotal: number;
  } | null;
}

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

export function UnitObjectiveSummaryList({
  objectives,
  testIDPrefix,
}: {
  objectives: UnitObjectiveSummary[];
  testIDPrefix?: string;
}): React.ReactElement | null {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();

  if (!Array.isArray(objectives) || objectives.length === 0) {
    return null;
  }

  const statusMeta = createStatusMeta(theme.colors);

  return (
    <View>
      {objectives.map(objective => {
        const meta = statusMeta[objective.status];
        const progressLabel =
          objective.progress && objective.progress.exercisesTotal > 0
            ? `${objective.progress.exercisesCorrect}/${objective.progress.exercisesTotal} correct`
            : meta.label;

        return (
          <View
            key={objective.id}
            style={styles.objectiveRow}
            testID={
              testIDPrefix ? `${testIDPrefix}-${objective.id}` : undefined
            }
          >
            <View
              style={[
                styles.objectiveStatusIcon,
                { backgroundColor: meta.background },
              ]}
            >
              <UiText
                style={[styles.objectiveStatusText, { color: meta.color }]}
              >
                {meta.icon}
              </UiText>
            </View>
            <View style={styles.objectiveTextContainer}>
              <UiText
                style={[styles.objectiveTitle, { color: theme.colors.text }]}
                numberOfLines={2}
                ellipsizeMode="tail"
              >
                {objective.title}
              </UiText>
              <UiText
                style={[
                  styles.objectiveSubtitle,
                  {
                    color: theme.colors.textSecondary,
                  },
                ]}
              >
                {progressLabel}
              </UiText>
            </View>
          </View>
        );
      })}
    </View>
  );
}

function createStatusMeta(colors: any): Record<LOStatus, ObjectiveStatusMeta> {
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
  container: { marginVertical: 8 },
  objectiveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  objectiveStatusIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  objectiveStatusText: {
    fontSize: 18,
    fontWeight: '600',
  },
  objectiveTextContainer: { flex: 1 },
  objectiveTitle: {
    fontSize: 15,
    fontWeight: '500',
  },
  objectiveSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
});
