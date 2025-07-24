/**
 * Topic List Screen for React Native Learning App
 *
 * Displays available learning topics with progress tracking
 * and navigation to individual learning sessions
 */

import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
  Alert,
  Modal,
  ScrollView,
  Platform
} from 'react-native'
import Animated, {
  FadeIn,
  SlideInUp,
  useAnimatedStyle,
  useSharedValue,
  withSpring
} from 'react-native-reanimated'

// Icons
import {
  BookOpen,
  Clock,
  Target,
  CheckCircle,
  ArrowRight,
  RefreshCw,
  Wifi,
  WifiOff,
  Code,
  X
} from 'lucide-react-native'

// Components
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Progress } from '@/components/ui/Progress'

// Services & Types
import { apiClient } from '@/services/api-client'
import { learningService } from '@/services/learning-service'
import { resetAppState } from '@/utils/debug'
import { colors, spacing, typography, shadows, responsive, textStyle } from '@/utils/theme'
import type {
  BiteSizedTopic,
  BiteSizedTopicDetail,
  TopicProgress,
  RootStackParamList
} from '@/types'
import type { NativeStackScreenProps } from '@react-navigation/native-stack'

type Props = NativeStackScreenProps<RootStackParamList, 'Learning'>

interface TopicItemProps {
  topic: BiteSizedTopic
  progress?: TopicProgress | null
  onPress: () => void
  isOfflineAvailable: boolean
  onDebugPress?: () => void
}

const TopicItem: React.FC<TopicItemProps> = ({
  topic,
  progress,
  onPress,
  isOfflineAvailable,
  onDebugPress
}) => {
  const scaleValue = useSharedValue(1)

  const handlePressIn = () => {
    scaleValue.value = withSpring(0.98)
  }

  const handlePressOut = () => {
    scaleValue.value = withSpring(1)
  }

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scaleValue.value }]
  }))

  const completionPercentage = progress?.completed ? 100 :
    (progress?.completedComponents.length || 0) / topic.component_count * 100

  return (
    <TouchableOpacity
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={0.8}
    >
      <Animated.View style={animatedStyle}>
        <Card style={styles.topicCard}>
          <View style={styles.topicHeader}>
            <View style={styles.topicInfo}>
              <Text style={styles.topicTitle}>{topic.title}</Text>
              <Text style={styles.topicDescription} numberOfLines={2}>
                {topic.description}
              </Text>
            </View>

            <View style={styles.topicMeta}>
              {!isOfflineAvailable && (
                <WifiOff size={16} color={colors.textSecondary} />
              )}
              {__DEV__ && onDebugPress && (
                <TouchableOpacity
                  onPress={onDebugPress}
                  style={styles.debugIconButton}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Code size={16} color={colors.info} />
                </TouchableOpacity>
              )}
              <ArrowRight size={20} color={colors.textSecondary} />
            </View>
          </View>

          <View style={styles.topicDetails}>
            <View style={styles.topicStats}>
              <View style={styles.statItem}>
                <Clock size={14} color={colors.textSecondary} />
                <Text style={styles.statText}>{topic.estimated_duration} min</Text>
              </View>

              <View style={styles.statItem}>
                <BookOpen size={14} color={colors.textSecondary} />
                <Text style={styles.statText}>{topic.component_count} steps</Text>
              </View>

              <View style={styles.statItem}>
                <Target size={14} color={colors.textSecondary} />
                <Text style={styles.statText}>Level {topic.difficulty}</Text>
              </View>
            </View>

            {/* Progress */}
            {progress && (
              <View style={styles.progressSection}>
                <View style={styles.progressHeader}>
                  <Text style={styles.progressText}>
                    {progress.completed ? 'Completed' : `${Math.round(completionPercentage)}% complete`}
                  </Text>
                  {progress.completed && (
                    <CheckCircle size={16} color={colors.success} />
                  )}
                </View>
                <Progress
                  value={completionPercentage}
                  color={progress.completed ? colors.success : colors.primary}
                  style={styles.progressBar}
                />
              </View>
            )}
          </View>
        </Card>
      </Animated.View>
    </TouchableOpacity>
  )
}

export default function TopicListScreen({ navigation }: Props) {
  const [topics, setTopics] = useState<BiteSizedTopic[]>([])
  const [topicProgress, setTopicProgress] = useState<Record<string, TopicProgress>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [debugModalVisible, setDebugModalVisible] = useState(false)
  const [debugTopic, setDebugTopic] = useState<BiteSizedTopicDetail | null>(null)
  const [debugLoading, setDebugLoading] = useState(false)

  useEffect(() => {
    loadTopics()
    loadProgress()
    checkNetworkStatus()
  }, [])

  const checkNetworkStatus = () => {
    setIsOnline(apiClient.networkStatus)
  }

  const loadTopics = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getBiteSizedTopics()
      setTopics(data)
    } catch (error) {
      console.warn('Failed to load topics:', error)
      Alert.alert(
        'Network Error',
        'Failed to load topics. Please check your connection and try again.',
        [
          { text: 'Retry', onPress: loadTopics },
          { text: 'Cancel', style: 'cancel' }
        ]
      )
    } finally {
      setIsLoading(false)
    }
  }

  const loadProgress = async () => {
    try {
      const progressData: Record<string, TopicProgress> = {}

      // Load progress for each topic (this could be optimized)
      for (const topic of topics) {
        const progress = await learningService.getTopicProgress(topic.id)
        if (progress) {
          progressData[topic.id] = progress
        }
      }

      setTopicProgress(progressData)
    } catch (error) {
      console.warn('Failed to load progress:', error)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([loadTopics(), loadProgress()])
    setIsRefreshing(false)
  }

  const handleTopicPress = async (topic: BiteSizedTopic) => {
    try {
      // Load detailed topic data
      const topicDetail = await learningService.loadTopic(topic.id)

      // Navigate to learning flow
      navigation.navigate('TopicDetail', {
        topicId: topic.id,
        topic: topicDetail
      })
    } catch (error) {
      console.warn('Failed to load topic detail:', error)
      Alert.alert(
        'Error',
        'Failed to load topic. Please try again.',
        [{ text: 'OK' }]
      )
    }
  }

  const renderTopic = ({ item, index }: { item: BiteSizedTopic; index: number }) => (
    <Animated.View
      entering={FadeIn.delay(index * 100)}
      style={styles.topicItemContainer}
    >
      <TopicItem
        topic={item}
        progress={topicProgress[item.id]}
        onPress={() => handleTopicPress(item)}
        isOfflineAvailable={learningService.isTopicAvailableOffline(item.id)}
        onDebugPress={__DEV__ ? () => handleDebugTopic(item) : undefined}
      />
    </Animated.View>
  )

    const handleClearCache = async () => {
    try {
      await resetAppState()
      Alert.alert(
        'Cache Cleared',
        'All learning data and cache has been reset. Pull to refresh to reload topics.',
        [{ text: 'OK' }]
      )
      // Refresh the screen
      setTopics([])
      setTopicProgress({})
      await handleRefresh()
    } catch (error) {
      Alert.alert(
        'Error',
        'Failed to clear cache. Please try again.',
        [{ text: 'OK' }]
      )
    }
  }

  const handleDebugTopic = async (topic: BiteSizedTopic) => {
    try {
      setDebugLoading(true)
      setDebugModalVisible(true)

      // Load the full topic detail with all components
      const fullTopic = await learningService.loadTopic(topic.id)
      setDebugTopic(fullTopic)
    } catch (error) {
      console.error('Failed to load topic detail for debug:', error)
      Alert.alert(
        'Debug Error',
        'Failed to load full topic details. Check console for details.',
        [{ text: 'OK' }]
      )
      setDebugModalVisible(false)
    } finally {
      setDebugLoading(false)
    }
  }

  const formatTopicPayload = (topic: BiteSizedTopicDetail) => {
    return JSON.stringify(topic, null, 2)
  }

  const renderHeader = () => (
    <Animated.View entering={SlideInUp} style={styles.header}>
      <Text style={styles.headerTitle}>Learning Topics</Text>
      <Text style={styles.headerSubtitle}>
        Choose a topic to start your learning journey
      </Text>

      {/* Network status indicator */}
      <View style={styles.networkStatus}>
        {isOnline ? (
          <View style={styles.onlineStatus}>
            <Wifi size={16} color={colors.success} />
            <Text style={[styles.statusText, { color: colors.success }]}>
              Online
            </Text>
          </View>
        ) : (
          <View style={styles.offlineStatus}>
            <WifiOff size={16} color={colors.warning} />
            <Text style={[styles.statusText, { color: colors.warning }]}>
              Offline Mode
            </Text>
          </View>
        )}
      </View>

      {/* Development only: Clear cache button */}
      {__DEV__ && (
        <Animated.View entering={SlideInUp.delay(300)} style={styles.debugSection}>
          <Button
            title="🗑️ Clear Cache"
            onPress={handleClearCache}
            variant="outline"
            size="small"
            style={styles.debugButton}
            textStyle={styles.debugButtonText}
          />
        </Animated.View>
      )}
    </Animated.View>
  )

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <BookOpen size={64} color={colors.textSecondary} />
      <Text style={styles.emptyTitle}>No Topics Available</Text>
      <Text style={styles.emptySubtitle}>
        {isOnline
          ? 'Check back later for new learning content.'
          : 'Connect to the internet to download topics.'
        }
      </Text>
              <Button
          title="Retry"
          onPress={loadTopics}
          variant="outline"
          icon={<RefreshCw size={16} color={colors.primary} />}
          style={styles.retryButton}
        />
    </View>
  )

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={topics}
        renderItem={renderTopic}
        keyExtractor={item => item.id}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={!isLoading ? renderEmpty : null}
        contentContainerStyle={[
          styles.listContent,
          topics.length === 0 && styles.emptyListContent
        ]}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      />

      {/* Debug Modal */}
      {__DEV__ && (
        <Modal
          visible={debugModalVisible}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setDebugModalVisible(false)}
        >
          <SafeAreaView style={styles.debugModalContainer}>
            <View style={styles.debugModalHeader}>
              <Text style={styles.debugModalTitle}>Topic Payload Debug</Text>
              <TouchableOpacity
                onPress={() => setDebugModalVisible(false)}
                style={styles.debugModalCloseButton}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <X size={24} color={colors.text} />
              </TouchableOpacity>
            </View>

                        <View style={styles.debugModalContent}>
              {debugLoading ? (
                <View style={styles.debugLoadingContainer}>
                  <Text style={styles.debugLoadingText}>Loading full topic details...</Text>
                </View>
              ) : debugTopic ? (
                <>
                  <View style={styles.debugModalTopicInfo}>
                    <Text style={styles.debugModalTopicTitle}>{debugTopic.title}</Text>
                    <Text style={styles.debugModalTopicId}>ID: {debugTopic.id}</Text>
                    <Text style={styles.debugModalComponentCount}>
                      Components: {debugTopic.components?.length || 0}
                    </Text>
                  </View>

                  <ScrollView
                    style={styles.debugModalScrollView}
                    contentContainerStyle={styles.debugModalScrollContent}
                  >
                    <View style={styles.debugCodeContainer}>
                      <Text style={styles.debugCodeText}>
                        {formatTopicPayload(debugTopic)}
                      </Text>
                    </View>
                  </ScrollView>
                </>
              ) : (
                <View style={styles.debugLoadingContainer}>
                  <Text style={styles.debugLoadingText}>No topic data available</Text>
                </View>
              )}
            </View>
          </SafeAreaView>
        </Modal>
      )}
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  listContent: {
    padding: spacing.lg,
  },

  emptyListContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },

  header: {
    marginBottom: spacing.xl,
  },

  headerTitle: textStyle({
    ...typography.heading1,
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.xs,
  }),

  headerSubtitle: textStyle({
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
  }),

  networkStatus: {
    alignItems: 'center',
  },

  onlineStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${colors.success}10`,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 16,
  },

  offlineStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${colors.warning}10`,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 16,
  },

  statusText: textStyle({
    ...typography.caption,
    fontWeight: '600',
    marginLeft: spacing.xs,
  }),

  topicItemContainer: {
    marginBottom: spacing.md,
  },

  topicCard: {
    padding: spacing.lg,
  },

  topicHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },

  topicInfo: {
    flex: 1,
    marginRight: spacing.md,
  },

  topicTitle: textStyle({
    ...typography.heading3,
    color: colors.text,
    marginBottom: spacing.xs,
  }),

  topicDescription: textStyle({
    ...typography.body,
    color: colors.textSecondary,
    lineHeight: 22,
  }),

  topicMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },

  topicDetails: {
    gap: spacing.md,
  },

  topicStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },

  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },

  statText: textStyle({
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  }),

  progressSection: {
    gap: spacing.xs,
  },

  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  progressText: textStyle({
    ...typography.caption,
    color: colors.text,
    fontWeight: '600',
  }),

  progressBar: {
    height: 4,
  },

  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },

  emptyTitle: textStyle({
    ...typography.heading2,
    color: colors.text,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
    textAlign: 'center',
  }),

  emptySubtitle: textStyle({
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
  }),

  retryButton: {
    paddingHorizontal: spacing.xl,
  },

  debugSection: {
    marginTop: spacing.lg,
    alignItems: 'center',
  },

  debugButton: {
    borderColor: colors.warning,
    backgroundColor: `${colors.warning}10`,
    paddingHorizontal: spacing.lg,
  },

  debugButtonText: {
    color: colors.warning,
    fontSize: 12,
    fontWeight: '500',
  },

  debugIconButton: {
    padding: spacing.xs,
    marginRight: spacing.xs,
  },

  debugModalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },

  debugModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
  },

  debugModalTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: colors.text,
  },

  debugModalCloseButton: {
    padding: spacing.xs,
  },

  debugModalContent: {
    flex: 1,
  },

  debugModalTopicInfo: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },

  debugModalTopicTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },

  debugModalTopicId: {
    fontSize: 14,
    color: colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: spacing.xs,
  },

  debugModalComponentCount: {
    fontSize: 14,
    color: colors.info,
    fontWeight: '600',
  },

  debugLoadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },

  debugLoadingText: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
  },

  debugModalScrollView: {
    flex: 1,
  },

  debugModalScrollContent: {
    padding: spacing.lg,
  },

  debugCodeContainer: {
    backgroundColor: colors.text + '05',
    borderRadius: 8,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },

  debugCodeText: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 12,
    lineHeight: 18,
    color: colors.text,
  },
})