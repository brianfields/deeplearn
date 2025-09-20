import React, { useMemo } from 'react';
import {
  View,
  Text,
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

type UnitDetailScreenNavigationProp = NativeStackNavigationProp<
  LearningStackParamList,
  'UnitDetail'
>;

export function UnitDetailScreen() {
  const route = useRoute<RouteProp<LearningStackParamList, 'UnitDetail'>>();
  const unitId = route.params?.unitId as string | undefined;
  const navigation = useNavigation<UnitDetailScreenNavigationProp>();
  const { data: unit } = useUnit(unitId || '');
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
      <SafeAreaView style={styles.container}>
        <Text style={styles.title}>Unit not found</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>{unit.title}</Text>
      {nextLessonTitle && (
        <View style={styles.resumeContainer}>
          <Text style={styles.resumeLabel}>Resume next:</Text>
          <Text style={styles.resumeTitle}>{nextLessonTitle}</Text>
        </View>
      )}
      {overallProgress && <UnitProgressView progress={overallProgress} />}
      <Text style={styles.subtitle}>Lessons</Text>
      <FlatList
        data={unit.lessons}
        keyExtractor={l => l.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => handleLessonPress(item.id)}
            style={styles.lessonRow}
            testID={`lesson-card`}
          >
            <Text style={styles.lessonTitle}>{item.title}</Text>
            <View style={styles.lessonRight}>
              {progressLS && (
                <Text style={styles.progressText}>
                  {Math.round(
                    progressLS.lessons.find(lp => lp.lessonId === item.id)
                      ?.progressPercentage || 0
                  )}
                  %
                </Text>
              )}
              <Text style={styles.lessonMeta}>
                {item.estimatedDuration} min
              </Text>
            </View>
          </TouchableOpacity>
        )}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB', padding: 20 },
  title: { fontSize: 24, fontWeight: '700', color: '#111827' },
  subtitle: { fontSize: 16, color: '#6B7280', marginTop: 16 },
  lessonRow: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginTop: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  lessonTitle: { fontSize: 16, color: '#111827', flex: 1, marginRight: 12 },
  lessonRight: { alignItems: 'flex-end' },
  lessonMeta: { fontSize: 12, color: '#6B7280' },
  progressText: { fontSize: 12, color: '#2563EB', marginBottom: 4 },
  listContent: { paddingVertical: 8 },
  resumeContainer: {
    backgroundColor: '#DBEAFE',
    borderRadius: 10,
    padding: 12,
    marginTop: 12,
  },
  resumeLabel: { fontSize: 12, color: '#1D4ED8' },
  resumeTitle: { fontSize: 14, color: '#1F2937', fontWeight: '600' },
});
