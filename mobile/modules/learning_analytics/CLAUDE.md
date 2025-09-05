# Learning Analytics Module (Frontend)

## Purpose

This frontend module provides user interfaces for learning analytics, progress visualization, and achievement tracking. It displays historical learning data and insights without managing active learning sessions or topic discovery.

## Domain Responsibility

**"Learning progress visualization and analytics user interface"**

The Learning Analytics frontend module owns all UI aspects of learning analytics:

- Progress visualization and dashboard interfaces
- Achievement and streak display
- Learning insights and recommendations
- Goal setting and tracking interfaces
- Historical learning data presentation
- Performance analytics and charts

## Architecture

### Module API (Public Interface)

```typescript
// module_api/index.ts
export { useLearningAnalytics } from './queries';
export { useLearningAnalyticsStore } from './store';
export { useLearningAnalyticsNavigation } from './navigation';
export type {
  TopicProgress,
  OverallProgress,
  LearningStreaks,
  Achievement,
} from './types';

// module_api/queries.ts
export function useLearningAnalytics() {
  return {
    useOverallProgress: (userId: string) =>
      useQuery({
        queryKey: ['analytics', userId, 'overall'],
        queryFn: () => getOverallProgressUseCase(userId),
        staleTime: 2 * 60 * 1000, // 2 minutes
        select: data => ProgressFormatter.formatOverallProgress(data),
      }),

    useTopicProgress: (userId: string, topicId: string) =>
      useQuery({
        queryKey: ['analytics', userId, 'topic', topicId],
        queryFn: () => getTopicProgressUseCase(userId, topicId),
        select: data => ProgressFormatter.formatTopicProgress(data),
      }),

    useLearningStreaks: (userId: string) =>
      useQuery({
        queryKey: ['analytics', userId, 'streaks'],
        queryFn: () => getLearningStreaksUseCase(userId),
        select: data => StreakFormatter.formatStreaks(data),
      }),

    useAchievements: (userId: string) =>
      useQuery({
        queryKey: ['analytics', userId, 'achievements'],
        queryFn: () => getAchievementsUseCase(userId),
        select: data => data.map(AchievementFormatter.formatAchievement),
      }),

    // Convenience method for other modules to get progress data
    getTopicProgress: (topicId: string) => {
      const queryClient = useQueryClient();
      return queryClient.getQueryData([
        'analytics',
        'current-user',
        'topic',
        topicId,
      ]);
    },
  };
}

// module_api/navigation.ts
export function useLearningAnalyticsNavigation() {
  const navigation = useNavigation();

  return {
    navigateToProgressDashboard: () =>
      navigation.navigate('LearningAnalytics', { screen: 'Dashboard' }),

    navigateToTopicAnalytics: (topicId: string) =>
      navigation.navigate('LearningAnalytics', {
        screen: 'TopicAnalytics',
        params: { topicId },
      }),

    navigateToAchievements: () =>
      navigation.navigate('LearningAnalytics', { screen: 'Achievements' }),
  };
}
```

### Screens (UI Layer)

```typescript
// screens/ProgressDashboard.tsx
export function ProgressDashboard() {
  const userId = 'current-user' // TODO: Get from auth
  const { useOverallProgress, useLearningStreaks } = useLearningAnalytics()

  const { data: overallProgress, isLoading: progressLoading } = useOverallProgress(userId)
  const { data: streaks, isLoading: streaksLoading } = useLearningStreaks(userId)

  if (progressLoading || streaksLoading) {
    return <LoadingScreen message="Loading your progress..." />
  }

  return (
    <ScrollView style={styles.container}>
      <DashboardHeader progress={overallProgress} />

      <Section title="Learning Progress">
        <OverallProgressCard progress={overallProgress} />
        <TopicsCompletedChart data={overallProgress.topicsCompleted} />
      </Section>

      <Section title="Learning Streaks">
        <CurrentStreakCard streak={streaks.currentStreak} />
        <StreakCalendar monthlyActivity={streaks.monthlyActivity} />
      </Section>

      <Section title="Recent Activity">
        <RecentSessionsList sessions={overallProgress.recentSessions} />
      </Section>

      <Section title="Goals">
        <LearningGoals goals={overallProgress.goals} />
      </Section>
    </ScrollView>
  )
}

// screens/TopicAnalyticsScreen.tsx
export function TopicAnalyticsScreen({ route }: Props) {
  const { topicId } = route.params
  const userId = 'current-user'
  const { useTopicProgress } = useLearningAnalytics()

  const { data: progress, isLoading } = useTopicProgress(userId, topicId)

  if (isLoading) {
    return <LoadingScreen />
  }

  if (!progress) {
    return <EmptyState message="No progress data available for this topic" />
  }

  return (
    <ScrollView style={styles.container}>
      <TopicProgressHeader progress={progress} />

      <Section title="Performance">
        <ScoreChart scores={progress.sessionScores} />
        <TimeSpentChart timeData={progress.timeSpentData} />
      </Section>

      <Section title="Mastery Progress">
        <MasteryLevelIndicator level={progress.masteryLevel} />
        <ComponentMastery components={progress.componentMastery} />
      </Section>

      <Section title="Session History">
        <SessionHistoryList sessions={progress.sessions} />
      </Section>
    </ScrollView>
  )
}

// screens/AchievementsScreen.tsx
export function AchievementsScreen() {
  const userId = 'current-user'
  const { useAchievements } = useLearningAnalytics()

  const { data: achievements, isLoading } = useAchievements(userId)

  const earnedAchievements = achievements?.filter(a => a.isEarned) || []
  const availableAchievements = achievements?.filter(a => !a.isEarned) || []

  return (
    <ScrollView style={styles.container}>
      <AchievementsHeader
        earnedCount={earnedAchievements.length}
        totalCount={achievements?.length || 0}
      />

      <Section title="Earned Achievements">
        <AchievementGrid achievements={earnedAchievements} />
      </Section>

      <Section title="Available Achievements">
        <AchievementGrid
          achievements={availableAchievements}
          showProgress={true}
        />
      </Section>
    </ScrollView>
  )
}
```

### Components (Analytics Components)

```typescript
// components/OverallProgressCard.tsx
interface OverallProgressCardProps {
  progress: OverallProgress
}

export function OverallProgressCard({ progress }: OverallProgressCardProps) {
  const completionRate = ProgressRules.calculateCompletionRate(progress)
  const learningVelocity = ProgressRules.formatVelocity(progress.learningVelocity)

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Overall Progress</Text>
        <Text style={styles.completionRate}>{completionRate}%</Text>
      </View>

      <View style={styles.stats}>
        <StatItem
          label="Topics Completed"
          value={progress.topicsCompleted}
          icon="check-circle"
        />
        <StatItem
          label="Total Time"
          value={TimeFormatter.formatDuration(progress.totalTimeSpent)}
          icon="clock"
        />
        <StatItem
          label="Average Score"
          value={`${Math.round(progress.averageScore * 100)}%`}
          icon="star"
        />
        <StatItem
          label="Learning Velocity"
          value={learningVelocity}
          icon="trending-up"
        />
      </View>

      <ProgressBar
        progress={completionRate / 100}
        color={ProgressRules.getProgressColor(completionRate)}
      />
    </Card>
  )
}

// components/CurrentStreakCard.tsx
interface CurrentStreakCardProps {
  streak: number
}

export function CurrentStreakCard({ streak }: CurrentStreakCardProps) {
  const streakMessage = StreakRules.getStreakMessage(streak)
  const streakColor = StreakRules.getStreakColor(streak)

  return (
    <Card style={[styles.card, { borderLeftColor: streakColor }]}>
      <View style={styles.content}>
        <Icon name="fire" size={32} color={streakColor} />
        <View style={styles.textContent}>
          <Text style={styles.streakNumber}>{streak}</Text>
          <Text style={styles.streakLabel}>Day Streak</Text>
          <Text style={styles.streakMessage}>{streakMessage}</Text>
        </View>
      </View>
    </Card>
  )
}

// components/AchievementBadge.tsx
interface AchievementBadgeProps {
  achievement: Achievement
  size?: 'small' | 'medium' | 'large'
  showProgress?: boolean
}

export function AchievementBadge({
  achievement,
  size = 'medium',
  showProgress = false
}: AchievementBadgeProps) {
  const badgeStyle = AchievementRules.getBadgeStyle(achievement, size)
  const progressPercentage = showProgress ?
    AchievementRules.calculateProgress(achievement) : null

  return (
    <TouchableOpacity
      style={[styles.badge, badgeStyle]}
      onPress={() => showAchievementDetail(achievement)}
    >
      <View style={styles.iconContainer}>
        <Icon
          name={achievement.icon}
          size={badgeStyle.iconSize}
          color={achievement.isEarned ? '#FFD700' : '#CCC'}
        />
      </View>

      <Text style={[styles.title, { opacity: achievement.isEarned ? 1 : 0.6 }]}>
        {achievement.title}
      </Text>

      {showProgress && progressPercentage !== null && (
        <View style={styles.progressContainer}>
          <ProgressBar
            progress={progressPercentage / 100}
            height={4}
            color="#4CAF50"
          />
          <Text style={styles.progressText}>{progressPercentage}%</Text>
        </View>
      )}
    </TouchableOpacity>
  )
}
```

### Application Layer (Use Cases)

```typescript
// application/getOverallProgress.usecase.ts
export async function getOverallProgressUseCase(
  userId: string
): Promise<OverallProgress> {
  try {
    // Get progress data from API
    const progressData = await learningAnalyticsApi.getOverallProgress(userId);

    // Enhance with calculated metrics
    const enhancedProgress =
      ProgressCalculator.enhanceProgressData(progressData);

    // Cache for offline access
    await ProgressCacheAdapter.cacheOverallProgress(userId, enhancedProgress);

    // Track analytics
    AnalyticsAdapter.track('progress_viewed', {
      userId,
      topicsCompleted: enhancedProgress.topicsCompleted,
      averageScore: enhancedProgress.averageScore,
    });

    return enhancedProgress;
  } catch (error) {
    // Fallback to cached data
    const cachedProgress =
      await ProgressCacheAdapter.getCachedOverallProgress(userId);
    if (cachedProgress) {
      return cachedProgress;
    }
    throw error;
  }
}

// application/recordSessionCompletion.usecase.ts
export async function recordSessionCompletionUseCase(
  sessionResults: SessionResults
): Promise<void> {
  try {
    // Send to analytics API
    await learningAnalyticsApi.recordSession(sessionResults);

    // Update local progress cache
    await ProgressCacheAdapter.updateProgressFromSession(sessionResults);

    // Check for new achievements
    const newAchievements = await AchievementCalculator.checkNewAchievements(
      sessionResults.userId,
      sessionResults
    );

    // Show achievement notifications
    if (newAchievements.length > 0) {
      NotificationAdapter.showAchievementUnlocked(newAchievements);
    }

    // Update streaks
    await StreakCalculator.updateStreaks(
      sessionResults.userId,
      sessionResults.completionTime
    );
  } catch (error) {
    // Queue for retry when online
    await OfflineQueueAdapter.queueSessionResult(sessionResults);
    throw error;
  }
}
```

### Domain Layer (Business Rules)

```typescript
// domain/business-rules/progress-rules.ts
export class ProgressRules {
  static calculateCompletionRate(progress: OverallProgress): number {
    if (progress.topicsStarted === 0) return 0;
    return Math.round(
      (progress.topicsCompleted / progress.topicsStarted) * 100
    );
  }

  static getProgressColor(completionRate: number): string {
    if (completionRate >= 80) return '#4CAF50'; // Green
    if (completionRate >= 60) return '#FF9800'; // Orange
    if (completionRate >= 40) return '#FFC107'; // Amber
    return '#F44336'; // Red
  }

  static formatVelocity(velocity: number): string {
    if (velocity >= 1) {
      return `${Math.round(velocity)} topics/week`;
    } else {
      const daysPerTopic = Math.round(7 / velocity);
      return `1 topic/${daysPerTopic} days`;
    }
  }

  static calculateMasteryLevel(topicProgress: TopicProgress): MasteryLevel {
    const { bestScore, sessionsCompleted, totalTimeSpent, targetTime } =
      topicProgress;

    if (bestScore >= 0.9 && sessionsCompleted >= 2) {
      return MasteryLevel.MASTERED;
    } else if (bestScore >= 0.7 && sessionsCompleted >= 1) {
      return MasteryLevel.PROFICIENT;
    } else if (sessionsCompleted > 0) {
      return MasteryLevel.LEARNING;
    } else {
      return MasteryLevel.NOT_STARTED;
    }
  }
}

// domain/business-rules/streak-rules.ts
export class StreakRules {
  static getStreakMessage(streak: number): string {
    if (streak === 0) return 'Start your learning journey!';
    if (streak === 1) return 'Great start! Keep it up!';
    if (streak < 7) return 'Building momentum!';
    if (streak < 30) return "You're on fire! 🔥";
    if (streak < 100) return 'Incredible dedication!';
    return 'Legendary learner! 🏆';
  }

  static getStreakColor(streak: number): string {
    if (streak === 0) return '#9E9E9E';
    if (streak < 7) return '#FF9800';
    if (streak < 30) return '#FF5722';
    return '#F44336';
  }

  static calculateConsistency(monthlyActivity: Record<string, number>): number {
    const totalDays = Object.keys(monthlyActivity).length;
    const activeDays = Object.values(monthlyActivity).filter(
      count => count > 0
    ).length;

    return totalDays > 0 ? Math.round((activeDays / totalDays) * 100) : 0;
  }
}

// domain/business-rules/achievement-rules.ts
export class AchievementRules {
  static checkStreakAchievements(currentStreak: number): Achievement[] {
    const achievements: Achievement[] = [];

    const streakMilestones = [
      { days: 3, id: 'STREAK_3', title: '3-Day Streak', icon: 'fire' },
      { days: 7, id: 'STREAK_7', title: 'Week Warrior', icon: 'fire' },
      { days: 30, id: 'STREAK_30', title: 'Monthly Master', icon: 'fire' },
      { days: 100, id: 'STREAK_100', title: 'Century Scholar', icon: 'fire' },
    ];

    streakMilestones.forEach(milestone => {
      if (currentStreak >= milestone.days) {
        achievements.push({
          id: milestone.id,
          title: milestone.title,
          description: `Maintained a ${milestone.days}-day learning streak`,
          icon: milestone.icon,
          isEarned: true,
          earnedDate: new Date(),
        });
      }
    });

    return achievements;
  }

  static calculateProgress(achievement: Achievement): number {
    // Calculate progress toward achievement based on current stats
    switch (achievement.type) {
      case 'streak':
        return Math.min(
          (achievement.currentValue / achievement.targetValue) * 100,
          100
        );
      case 'mastery':
        return Math.min(
          (achievement.currentValue / achievement.targetValue) * 100,
          100
        );
      default:
        return 0;
    }
  }
}
```

### Navigation (Module Stack)

```typescript
// navigation/LearningAnalyticsStack.tsx
const Stack = createNativeStackNavigator<LearningAnalyticsStackParamList>()

export function LearningAnalyticsStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="Dashboard"
        component={ProgressDashboard}
        options={{ title: 'Your Progress' }}
      />
      <Stack.Screen
        name="TopicAnalytics"
        component={TopicAnalyticsScreen}
        options={{ title: 'Topic Analytics' }}
      />
      <Stack.Screen
        name="Achievements"
        component={AchievementsScreen}
        options={{ title: 'Achievements' }}
      />
    </Stack.Navigator>
  )
}
```

## Cross-Module Communication

### Provides to Other Modules

- **Topic Catalog Module**: Progress data for topic display
- **Learning Session Module**: Historical context for sessions

### Dependencies

- **Learning Session Module**: Session results for progress calculation
- **Infrastructure Module**: HTTP client, storage, notifications

### Communication Examples

```typescript
// Provide progress data to Topic Catalog module
const { getTopicProgress } = useLearningAnalytics();
const progress = getTopicProgress(topicId);
// Topic Catalog uses this for progress indicators on topic cards

// Receive session results from Learning Session module
// This happens automatically when sessions complete
// The analytics API records the session data
```

## Testing Strategy

### Screen Tests (UI Behavior)

```typescript
// tests/screens/ProgressDashboard.test.tsx
const mockProgress = {
  topicsCompleted: 5,
  topicsStarted: 8,
  averageScore: 0.85,
  totalTimeSpent: 3600
}

jest.mock('../../module_api', () => ({
  useLearningAnalytics: () => ({
    useOverallProgress: () => ({ data: mockProgress, isLoading: false })
  })
}))

describe('ProgressDashboard', () => {
  it('displays overall progress correctly', () => {
    render(<ProgressDashboard />, { wrapper: TestWrapper })

    expect(screen.getByText('5')).toBeTruthy() // Topics completed
    expect(screen.getByText('85%')).toBeTruthy() // Average score
  })
})
```

### Domain Tests (Business Logic)

```typescript
// tests/domain/progress-rules.test.ts
describe('ProgressRules', () => {
  it('calculates completion rate correctly', () => {
    const progress = { topicsCompleted: 3, topicsStarted: 10 };

    const rate = ProgressRules.calculateCompletionRate(progress);

    expect(rate).toBe(30);
  });

  it('determines mastery level correctly', () => {
    const topicProgress = {
      bestScore: 0.95,
      sessionsCompleted: 3,
      totalTimeSpent: 1800,
    };

    const level = ProgressRules.calculateMasteryLevel(topicProgress);

    expect(level).toBe(MasteryLevel.MASTERED);
  });
});
```

## Performance Optimizations

### Data Caching

- **Progress Caching**: Cache progress data for offline viewing
- **Chart Data**: Pre-calculate chart data for smooth rendering
- **Achievement Status**: Cache achievement status locally

### UI Optimizations

- **Lazy Loading**: Load detailed analytics only when needed
- **Chart Optimization**: Use efficient charting libraries
- **Image Caching**: Cache achievement badges and icons

## Anti-Patterns to Avoid

❌ **Active session management** (belongs in Learning Session module)
❌ **Topic browsing/selection** (belongs in Catalog module)
❌ **Business logic in screen components**
❌ **Real-time session state management**
❌ **Content creation functionality**

## Module Evolution

This module can be extended with:

- **Advanced Analytics**: Detailed learning insights, predictive analytics
- **Social Features**: Leaderboards, peer comparisons, sharing
- **Goal Management**: Custom learning goals, milestone tracking
- **Export Features**: Progress reports, certificates, data export
- **Gamification**: Points, levels, challenges, rewards

The modular architecture ensures these features can be added without affecting active learning or topic discovery functionality.
