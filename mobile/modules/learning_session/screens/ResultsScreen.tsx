/**
 * Results Screen - Learning Objective Progress Overview
 *
 * Displays unit-wide learning objective progress after completing a lesson.
 * Works fully offline by relying on cached lesson/session data and local LO
 * progress aggregation.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, ScrollView } from 'react-native';
import { CheckCircle } from 'lucide-react-native';
import Animated, { FadeIn, Easing } from 'react-native-reanimated';

import { reducedMotion } from '../../ui_system/utils/motion';
import { animationTimings } from '../../ui_system/utils/animations';
import {
  Button,
  Card,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { LOProgressList } from '../components/LOProgressList';
import { catalogProvider } from '../../catalog/public';
import { DEFAULT_ANONYMOUS_USER_ID, useAuth } from '../../user/public';
import { useUnitLOProgress, useNextLessonToResume } from '../queries';
import type { LearningStackParamList } from '../../../types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { LOProgressItem as LOProgressRecord } from '../models';

import type { LessonDetail } from '../../catalog/models';

type Props = NativeStackScreenProps<LearningStackParamList, 'Results'>;

type SummaryMetrics = {
  readonly total: number;
  readonly completed: number;
  readonly partial: number;
  readonly notStarted: number;
  readonly newlyCompleted: number;
};

export default function ResultsScreen({ navigation, route }: Props) {
  const { results, unitId } = route.params;
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { spacing, typography, colors } = theme;
  const haptics = useHaptics();
  const { user } = useAuth();
  const userKey = user?.id ? String(user.id) : DEFAULT_ANONYMOUS_USER_ID;
  const [isContinuePending, setIsContinuePending] = useState(false);
  const [isRetryPending, setIsRetryPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const catalog = useMemo(() => catalogProvider(), []);

  useEffect(() => {
    haptics.trigger('success');
  }, [haptics]);

  const { data: latestProgress, isFetching: isProgressFetching } =
    useUnitLOProgress(userKey, unitId, {
      enabled: Boolean(unitId),
      staleTime: 30 * 1000,
    });

  const { data: nextLessonId, isFetching: isNextLessonLoading } =
    useNextLessonToResume(userKey, unitId, {
      enabled: Boolean(unitId),
      staleTime: 60 * 1000,
    });

  const newlyCompletedSet = useMemo(() => {
    const fromResults = results.unitLOProgress?.items ?? [];
    return new Set(
      fromResults
        .filter(item => item.newlyCompletedInSession)
        .map(item => item.loId)
    );
  }, [results.unitLOProgress]);

  const progressItems: LOProgressRecord[] = useMemo(() => {
    const sourceItems =
      latestProgress?.items ?? results.unitLOProgress?.items ?? [];
    return sourceItems.map(item => ({
      ...item,
      newlyCompletedInSession: newlyCompletedSet.has(item.loId),
    }));
  }, [latestProgress?.items, newlyCompletedSet, results.unitLOProgress]);

  const summary: SummaryMetrics = useMemo(() => {
    const total = progressItems.length;
    const completed = progressItems.filter(
      item => item.status === 'completed'
    ).length;
    const partial = progressItems.filter(
      item => item.status === 'partial'
    ).length;
    const notStarted = progressItems.filter(
      item => item.status === 'not_started'
    ).length;
    const newlyCompleted = progressItems.filter(
      item => item.newlyCompletedInSession
    ).length;
    return { total, completed, partial, notStarted, newlyCompleted };
  }, [progressItems]);

  const summaryHeadline = useMemo(() => {
    if (!summary.total) {
      return 'Lesson complete!';
    }
    return `You have mastered ${summary.completed} of ${summary.total} objectives`;
  }, [summary.completed, summary.total]);

  const summarySubhead = useMemo(() => {
    if (summary.newlyCompleted > 0) {
      return `Great work! ${summary.newlyCompleted} objective${
        summary.newlyCompleted === 1 ? '' : 's'
      } mastered for the first time this lesson.`;
    }
    if (summary.partial > 0) {
      return 'Keep going to finish the remaining objectives.';
    }
    return 'Review or continue learning to build more progress.';
  }, [summary.newlyCompleted, summary.partial]);

  const canContinue = Boolean(nextLessonId);

  const loadLessonDetail = useCallback(
    async (lessonId: string): Promise<LessonDetail | null> => {
      try {
        const detail = await catalog.getLessonDetail(lessonId);
        return detail;
      } catch (error) {
        console.warn('[ResultsScreen] Failed to load lesson detail', {
          lessonId,
          error,
        });
        return null;
      }
    },
    [catalog]
  );

  const handleContinue = useCallback(async () => {
    if (!canContinue || !nextLessonId) {
      navigation.navigate('UnitDetail', { unitId });
      return;
    }

    setActionError(null);
    setIsContinuePending(true);
    const detail = await loadLessonDetail(nextLessonId);
    if (!detail) {
      setActionError('Unable to load the next lesson while offline.');
      setIsContinuePending(false);
      return;
    }

    navigation.replace('LearningFlow', {
      lessonId: nextLessonId,
      lesson: detail,
      unitId,
    });
    setIsContinuePending(false);
  }, [canContinue, loadLessonDetail, navigation, nextLessonId, unitId]);

  const handleRetry = useCallback(async () => {
    setActionError(null);
    setIsRetryPending(true);
    const detail = await loadLessonDetail(results.lessonId);
    if (!detail) {
      setActionError('This lesson is unavailable offline right now.');
      setIsRetryPending(false);
      return;
    }

    navigation.replace('LearningFlow', {
      lessonId: results.lessonId,
      lesson: detail,
      unitId,
    });
    setIsRetryPending(false);
  }, [loadLessonDetail, navigation, results.lessonId, unitId]);

  const handleBackToUnit = useCallback(() => {
    navigation.navigate('UnitDetail', { unitId });
  }, [navigation, unitId]);

  const contentStyles = useMemo(
    () =>
      StyleSheet.create({
        container: {
          flex: 1,
          backgroundColor: colors.background,
        },
        scrollContent: {
          flexGrow: 1,
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.lg,
          paddingBottom: spacing.xl,
        },
        header: {
          alignItems: 'center',
          gap: spacing.md,
          marginBottom: spacing.lg,
        },
        iconContainer: {
          width: 84,
          height: 84,
          borderRadius: 42,
          backgroundColor: colors.success,
          alignItems: 'center',
          justifyContent: 'center',
        },
        title: {
          fontSize: typography.heading2.fontSize,
          lineHeight: typography.heading2.lineHeight,
          color: colors.text,
          textAlign: 'center',
          fontWeight: '600',
        },
        subtitle: {
          fontSize: typography.body.fontSize,
          lineHeight: typography.body.lineHeight,
          color: colors.textSecondary,
          textAlign: 'center',
        },
        summaryCard: {
          marginBottom: spacing.lg,
          gap: spacing.sm,
        },
        summaryMetrics: {
          flexDirection: 'row',
          flexWrap: 'wrap',
          gap: spacing.sm,
        },
        metricPill: {
          paddingHorizontal: spacing.md,
          paddingVertical: spacing.xs,
          borderRadius: 999,
          backgroundColor: `${colors.primary}14`,
        },
        metricText: {
          color: colors.primary,
          fontSize: 14,
          fontWeight: '600',
        },
        sectionTitle: {
          fontSize: typography.heading3.fontSize,
          lineHeight: typography.heading3.lineHeight,
          color: colors.text,
          fontWeight: '600',
          marginBottom: spacing.md,
        },
        footer: {
          paddingHorizontal: spacing.lg,
          paddingBottom: spacing.lg,
          gap: spacing.sm,
        },
        errorText: {
          color: colors.error,
          textAlign: 'center',
        },
      }),
    [colors, spacing, typography]
  );

  return (
    <SafeAreaView style={contentStyles.container}>
      <ScrollView
        contentContainerStyle={contentStyles.scrollContent}
        testID="results-scroll"
      >
        <Animated.View
          entering={
            reducedMotion.enabled
              ? undefined
              : FadeIn.duration(animationTimings.ui).easing(
                  Easing.bezier(0.2, 0.8, 0.2, 1)
                )
          }
          style={contentStyles.header}
        >
          <View style={contentStyles.iconContainer}>
            <CheckCircle size={40} color={colors.surface} />
          </View>
          <Text style={contentStyles.title}>Lesson Complete!</Text>
          <Text style={contentStyles.subtitle}>{summaryHeadline}</Text>
          <Text style={contentStyles.subtitle}>{summarySubhead}</Text>
        </Animated.View>

        <Animated.View
          entering={
            reducedMotion.enabled
              ? undefined
              : FadeIn.delay(120)
                  .duration(animationTimings.ui)
                  .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
          }
        >
          <Card style={contentStyles.summaryCard} testID="results-summary">
            <Text
              style={contentStyles.sectionTitle}
              testID="results-summary-mastered"
            >
              {summaryHeadline}
            </Text>
            <View style={contentStyles.summaryMetrics}>
              <View style={contentStyles.metricPill}>
                <Text style={contentStyles.metricText}>
                  {summary.completed} mastered
                </Text>
              </View>
              <View style={contentStyles.metricPill}>
                <Text style={contentStyles.metricText}>
                  {summary.partial} in progress
                </Text>
              </View>
              <View style={contentStyles.metricPill}>
                <Text style={contentStyles.metricText}>
                  {summary.notStarted} not started
                </Text>
              </View>
            </View>
          </Card>
        </Animated.View>

        <Animated.View
          entering={
            reducedMotion.enabled
              ? undefined
              : FadeIn.delay(240)
                  .duration(animationTimings.ui)
                  .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
          }
        >
          <Text style={contentStyles.sectionTitle}>
            Learning Objective Progress
          </Text>
          <LOProgressList
            items={progressItems}
            isLoading={isProgressFetching}
            testID="results-lo-progress-list"
          />
        </Animated.View>
      </ScrollView>

      <View style={contentStyles.footer}>
        {actionError ? (
          <Text style={contentStyles.errorText}>{actionError}</Text>
        ) : null}

        {canContinue ? (
          <Button
            title="Continue to Next Lesson"
            onPress={() => {
              void handleContinue();
            }}
            variant="primary"
            size="large"
            loading={isContinuePending || isNextLessonLoading}
            disabled={isContinuePending || isNextLessonLoading}
            testID="results-continue-button"
          />
        ) : null}

        <Button
          title="Retry Lesson"
          onPress={() => {
            void handleRetry();
          }}
          variant="secondary"
          size="large"
          loading={isRetryPending}
          disabled={isRetryPending}
          testID="results-retry-button"
        />

        <Button
          title="Back to Unit Overview"
          onPress={handleBackToUnit}
          variant="tertiary"
          size="large"
          testID="results-back-button"
        />
      </View>
    </SafeAreaView>
  );
}
