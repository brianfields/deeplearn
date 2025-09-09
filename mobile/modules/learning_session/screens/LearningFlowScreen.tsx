/**
 * LearningFlowScreen - Navigation Wrapper for Learning Sessions
 *
 * This screen serves as the navigation layer for individual learning sessions.
 * It's a thin wrapper that handles navigation concerns while delegating the
 * actual learning logic to the LearningFlow component.
 *
 * NAVIGATION ARCHITECTURE ROLE:
 * - Entry point from the topic selection (TopicListScreen)
 * - Receives topic data via navigation route parameters
 * - Manages navigation transitions to/from learning sessions
 * - Handles completion navigation to ResultsScreen
 *
 * RESPONSIBILITY SEPARATION:
 * - Screen-level: Navigation, route handling, screen lifecycle
 * - Component-level: Learning logic, progress tracking, user interactions
 *
 * NAVIGATION FLOW:
 * TopicListScreen → LearningFlowScreen → ResultsScreen
 *                ↗ (via route params)   ↗ (via completion)
 *
 * KEY FUNCTIONS:
 * - Extracts topic data from navigation route parameters
 * - Provides navigation callbacks to LearningFlow component
 * - Handles completion by navigating to ResultsScreen with results
 * - Manages back navigation to topic list
 *
 * INTEGRATION POINTS:
 * - Receives BiteSizedTopicDetail from route.params
 * - Passes LearningResults to ResultsScreen
 * - Coordinates with React Navigation stack
 */

import { View, StyleSheet } from 'react-native';

// Components
import LearningFlow from '../components/LearningFlow';

// Types
import type { LearningResults, LearningStackParamList } from '@/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<LearningStackParamList, 'LearningFlow'>;

export default function LearningFlowScreen({ navigation, route }: Props) {
  const { topic } = route.params;

  const handleComplete = (results: LearningResults) => {
    // Navigate to results screen
    navigation.replace('Results', { results });
  };

  const handleBack = () => {
    // Navigate back to topic list
    navigation.goBack();
  };

  return (
    <View style={styles.container}>
      <LearningFlow
        sessionId={`session-${topic.id}`}
        onComplete={handleComplete}
        onBack={handleBack}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
