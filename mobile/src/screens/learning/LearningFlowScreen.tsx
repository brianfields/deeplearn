/**
 * Learning Flow Screen for React Native Learning App
 *
 * Wrapper screen for the DuolingoLearningFlow component
 * Handles navigation and screen-level state management
 */

import React from 'react'
import { View, StyleSheet } from 'react-native'

// Components
import DuolingoLearningFlow from '@/components/learning/DuolingoLearningFlow'

// Types
import type {
  LearningResults,
  LearningStackParamList
} from '@/types'
import type { NativeStackScreenProps } from '@react-navigation/native-stack'

type Props = NativeStackScreenProps<LearningStackParamList, 'LearningFlow'>

export default function LearningFlowScreen({ navigation, route }: Props) {
  const { topicId, topic } = route.params

  const handleComplete = (results: LearningResults) => {
    // Navigate to results screen
    navigation.replace('Results', { results })
  }

  const handleBack = () => {
    // Navigate back to topic list
    navigation.goBack()
  }

  return (
    <View style={styles.container}>
      <DuolingoLearningFlow
        topic={topic}
        onComplete={handleComplete}
        onBack={handleBack}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
})