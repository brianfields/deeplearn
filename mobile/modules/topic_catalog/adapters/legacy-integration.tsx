/**
 * Legacy integration adapter for Topic Catalog module.
 *
 * Provides compatibility layer between the new modular TopicListScreen
 * and the existing app structure, types, and navigation.
 */

import React from 'react';
import { Alert } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { TopicListScreen } from '../screens/TopicListScreen';
import { TopicSummary } from '../domain/entities/topic-summary';

// Import legacy screen for migration wrapper
import LegacyTopicListScreen from '../../../src/screens/learning/TopicListScreen';

// Import navigation types
import type { RootStackParamList } from '../../../src/types';

// Legacy types (these would be imported from existing app)
interface BiteSizedTopic {
  id: string;
  title: string;
  description: string;
  component_count: number;
  estimated_duration: number;
  user_level: string;
  created_at: string;
  updated_at: string;
}

type Props = NativeStackScreenProps<RootStackParamList, 'Learning'>;

/**
 * Adapter component that wraps the new TopicListScreen with legacy compatibility.
 */
export function LegacyTopicListScreenAdapter({ navigation }: Props) {
  const handleTopicPress = async (topic: TopicSummary) => {
    try {
      // Convert TopicSummary back to legacy format for navigation
      const legacyTopic: BiteSizedTopic = {
        id: topic.id,
        title: topic.title,
        description: topic.coreConcept,
        component_count: topic.componentCount,
        estimated_duration: topic.estimatedDuration,
        user_level: topic.userLevel,
        created_at: topic.createdAt,
        updated_at: topic.updatedAt,
      };

      // Navigate using legacy navigation structure
      navigation.navigate('TopicDetail', {
        topicId: topic.id,
        topic: legacyTopic as any, // Type assertion for legacy compatibility
      });
    } catch (error) {
      console.warn('Failed to navigate to topic:', error);
      Alert.alert('Error', 'Failed to load topic. Please try again.', [
        { text: 'OK' },
      ]);
    }
  };

  return (
    <TopicListScreen
      onTopicPress={handleTopicPress}
      baseUrl="http://localhost:8000" // TODO: Get from app config
      // apiKey={userToken} // TODO: Get from auth context
    />
  );
}

/**
 * Type conversion utilities for legacy compatibility.
 */
export class LegacyTypeConverter {
  /**
   * Convert legacy BiteSizedTopic to new TopicSummary.
   */
  static biteSizedTopicToTopicSummary(
    legacyTopic: BiteSizedTopic
  ): TopicSummary {
    return {
      id: legacyTopic.id,
      title: legacyTopic.title,
      coreConcept: legacyTopic.description,
      userLevel: legacyTopic.user_level as
        | 'beginner'
        | 'intermediate'
        | 'advanced',
      learningObjectives: [], // Not available in legacy format
      keyConcepts: [], // Not available in legacy format
      estimatedDuration: legacyTopic.estimated_duration,
      componentCount: legacyTopic.component_count,
      isReadyForLearning: legacyTopic.component_count > 0, // Infer from component count
      createdAt: legacyTopic.created_at,
      updatedAt: legacyTopic.updated_at,
      difficultyLevel: this.formatDifficultyLevel(legacyTopic.user_level),
      durationDisplay: this.formatDuration(legacyTopic.estimated_duration),
      readinessStatus: legacyTopic.component_count > 0 ? 'Ready' : 'Draft',
      tags: [], // Not available in legacy format
    };
  }

  /**
   * Convert new TopicSummary to legacy BiteSizedTopic.
   */
  static topicSummaryToBiteSizedTopic(topic: TopicSummary): BiteSizedTopic {
    return {
      id: topic.id,
      title: topic.title,
      description: topic.coreConcept,
      component_count: topic.componentCount,
      estimated_duration: topic.estimatedDuration,
      user_level: topic.userLevel,
      created_at: topic.createdAt,
      updated_at: topic.updatedAt,
    };
  }

  private static formatDifficultyLevel(userLevel: string): string {
    const levelMap: Record<string, string> = {
      beginner: 'Beginner',
      intermediate: 'Intermediate',
      advanced: 'Advanced',
    };
    return levelMap[userLevel] || 'Unknown';
  }

  private static formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} min`;
    }

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    if (remainingMinutes === 0) {
      return `${hours} hr`;
    }

    return `${hours} hr ${remainingMinutes} min`;
  }
}

/**
 * Migration helper to gradually replace legacy TopicListScreen.
 *
 * Usage:
 * 1. Replace import in navigation stack
 * 2. Update navigation types gradually
 * 3. Remove legacy screen when ready
 */
export function createMigrationWrapper(useLegacy: boolean = false) {
  if (useLegacy) {
    // Return legacy screen (to be imported from existing location)
    return LegacyTopicListScreen;
  } else {
    // Return new modular screen
    return LegacyTopicListScreenAdapter;
  }
}
