import React, { useMemo } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  FlatList,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useUnit } from '../queries';
import { UnitProgressView } from '../components/UnitProgress';
import type { LearningStackParamList } from '../../../types';
import {
  useUnitProgress as useUnitProgressLS,
  useNextLessonToResume,
} from '../../learning_session/queries';
import { catalogProvider } from '../public';
import {
  Box,
  Card,
  Text,
  Button,
  uiSystemProvider,
} from '../../ui_system/public';

type UnitDetailScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'UnitDetail'
>;

export function UnitDetailScreen() {
  const route = useRoute<RouteProp<LearningStackParamList, 'UnitDetail'>>();
  const unitId = route.params?.unitId as string | undefined;
  const navigation = useNavigation<UnitDetailScreenNavigationProp>();
  const { data: unit } = useUnit(unitId || '');
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  // For now, use anonymous user until auth is wired up
  const userId = 'anonymous';
  const { data: progressLS } = useUnitProgressLS(userId, unit?.id || '', {
    enabled: !!unit?.id,
    staleTime: 60 * 1000,
  });

  // Determine next lesson to resume within this unit
  const { data: nextLessonId } = useNextLessonToResume(userId, unit?.id || '', {
    enabled: !!unit?.id,
    staleTime: 60 * 1000,
  });

  // Map LS progress to Units progress view shape
  const overallProgress = useMemo(() => {
    if (!progressLS) return null;
    return {
      unitId: progressLS.unitId,
      completedLessons: progressLS.lessonsCompleted,
      totalLessons: progressLS.totalLessons,
      progressPercentage: Math.round(progressLS.progressPercentage),
    } as any;
  }, [progressLS]);

  const nextLessonTitle = useMemo(() => {
    if (!unit || !nextLessonId) return null;
    return unit.lessons.find(l => l.id === nextLessonId)?.title ?? null;
  }, [unit, nextLessonId]);

  const handleLessonPress = async (lessonId: string): Promise<void> => {
    try {
      const catalog = catalogProvider();
      const detail = await catalog.getLessonDetail(lessonId);
      if (!detail) {
        Alert.alert('Lesson not found', 'Unable to open this lesson.');
        return;
      }
      navigation.navigate('LearningFlow', {
        lessonId: detail.id,
        lesson: detail,
      });
    } catch {
      Alert.alert('Unable to open lesson', 'Please try again.');
    }
  };

  if (!unit) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <Box p="lg">
          <Text variant="h1">Unit not found</Text>
        </Box>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <Box p="lg" pb="sm">
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel="Go back"
          style={{ paddingVertical: 6, paddingRight: 12 }}
        >
          <Text variant="body" color={theme.colors.primary}>
            {'‹ Back'}
          </Text>
        </TouchableOpacity>
        <Text variant="h1" style={{ marginTop: 8 }}>
          {unit.title}
        </Text>
      </Box>

      <Box px="lg">
        <Card variant="default" style={{ margin: 0 }}>
          {nextLessonTitle && (
            <Box mb="md">
              <Text variant="secondary" color={theme.colors.textSecondary}>
                Resume next:
              </Text>
              <Text variant="title">{nextLessonTitle}</Text>
            </Box>
          )}

          {overallProgress && (
            <Box mb="md">
              <UnitProgressView progress={overallProgress} />
            </Box>
          )}

          <Button
            title={nextLessonTitle ? 'Resume Lesson' : 'Start Learning'}
            onPress={() => {
              const next = unit.lessons[0]?.id;
              if (next) {
                handleLessonPress(next);
              } else {
                Alert.alert('No lessons', 'This unit has no lessons yet.');
              }
            }}
            variant="primary"
            size="large"
            fullWidth
            testID="primary-cta"
          />
        </Card>
      </Box>

      <Box px="lg" mt="lg">
        <Text variant="title" style={{ marginBottom: 8 }}>
          Lessons
        </Text>
      </Box>

      <FlatList
        data={unit.lessons}
        keyExtractor={l => l.id}
        renderItem={({ item }) => (
          <Box px="lg" testID="lesson-card">
            <Card
              variant="outlined"
              style={{ margin: 0, marginBottom: 12 }}
              onPress={() => handleLessonPress(item.id)}
            >
              <View style={styles.lessonRowInner}>
                <Text variant="body" style={{ flex: 1, marginRight: 12 }}>
                  {item.title}
                </Text>
                <View style={styles.lessonRight}>
                  {progressLS && (
                    <Text variant="caption" color={theme.colors.accent}>
                      {Math.round(
                        progressLS.lessons.find(lp => lp.lessonId === item.id)
                          ?.progressPercentage || 0
                      )}
                      %
                    </Text>
                  )}
                  <Text variant="caption" color={theme.colors.textSecondary}>
                    {item.estimatedDuration} min
                  </Text>
                </View>
              </View>
            </Card>
          </Box>
        )}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  lessonRight: { alignItems: 'flex-end' },
  listContent: { paddingVertical: 8, paddingBottom: 24 },
  lessonRowInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
});
