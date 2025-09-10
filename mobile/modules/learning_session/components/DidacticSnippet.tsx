/**
 * DidacticSnippet Component - Educational Content Presentation
 *
 * Presents educational content in an engaging, mobile-optimized format.
 * Serves as the "teaching" phase of the learning experience.
 */

import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, Animated } from 'react-native';
import { Button, Card } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { useComponentState, useLearningSessionStore } from '../store';
import type { ComponentState } from '../models';

interface DidacticSnippetProps {
  component: ComponentState;
  onContinue: () => void;
  isLoading?: boolean;
}

interface DidacticContent {
  title: string;
  snippet: string;
  core_concept?: string;
  key_points?: string[];
  examples?: string[];
  estimated_duration?: number;
}

export default function DidacticSnippet({
  component,
  onContinue,
  isLoading = false,
}: DidacticSnippetProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

  // Component state management
  const { timeSpent } = useComponentState(component.id);
  const startComponent = useLearningSessionStore(s => s.startComponent);

  // Local state
  const [hasStartedReading, setHasStartedReading] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [showKeyPoints, setShowKeyPoints] = useState(false);
  const [showExamples, setShowExamples] = useState(false);

  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  // Extract content from component (align with backend field names)
  const raw: any = component.content || {};
  const title =
    (raw.title as string) || component.title || 'Educational Content';
  const snippet = (raw.explanation as string) || 'N/A.';
  const core_concept =
    (raw.core_concept as string) || (raw.coreConcept as string) || undefined;
  const key_points: string[] =
    (raw.key_points as string[]) || (raw.keyPoints as string[]) || [];
  const examples: string[] = (raw.examples as string[]) || [];
  const estimated_duration = (raw.estimated_duration as number) || undefined;

  // Start tracking when component mounts
  useEffect(() => {
    startComponent(component.id);

    // Animate content in
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
    // Run once per component id
  }, [component.id]);

  // Handle scroll progress
  const handleScroll = (event: any) => {
    const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
    const scrollPercentage =
      contentOffset.y / (contentSize.height - layoutMeasurement.height);
    const progress = Math.min(Math.max(scrollPercentage, 0), 1);

    setScrollProgress(progress);

    if (!hasStartedReading && progress > 0.1) {
      setHasStartedReading(true);
    }

    // Show key points after 30% scroll
    if (progress > 0.3 && !showKeyPoints && key_points.length > 0) {
      setShowKeyPoints(true);
    }

    // Show examples after 60% scroll
    if (progress > 0.6 && !showExamples && examples.length > 0) {
      setShowExamples(true);
    }
  };

  // Determine if user has engaged enough to continue
  const canContinue =
    hasStartedReading &&
    (scrollProgress > 0.8 || // Scrolled to near end
      timeSpent > (estimated_duration || 30) * 0.7 || // Spent 70% of estimated time
      timeSpent > 15); // Minimum 15 seconds

  // Render key points section
  const renderKeyPoints = () => {
    if (!key_points.length || !showKeyPoints) return null;

    return (
      <Animated.View
        style={[
          styles.sectionCard,
          {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }],
          },
        ]}
      >
        <Text style={styles.sectionTitle}>Key Points</Text>
        {key_points.map((point, index) => (
          <View key={index} style={styles.keyPointItem}>
            <View style={styles.keyPointBullet} />
            <Text style={styles.keyPointText}>{point}</Text>
          </View>
        ))}
      </Animated.View>
    );
  };

  // Render examples section
  const renderExamples = () => {
    if (!examples.length || !showExamples) return null;

    return (
      <Animated.View
        style={[
          styles.sectionCard,
          {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }],
          },
        ]}
      >
        <Text style={styles.sectionTitle}>Examples</Text>
        {examples.map((example, index) => (
          <Card key={index} style={styles.exampleCard}>
            <Text style={styles.exampleText}>{example}</Text>
          </Card>
        ))}
      </Animated.View>
    );
  };

  // Render core concept highlight
  const renderCoreConcept = () => {
    if (!core_concept) return null;

    return (
      <Card style={styles.conceptCard}>
        <Text style={styles.conceptLabel}>Core Concept</Text>
        <Text style={styles.conceptText}>{core_concept}</Text>
      </Card>
    );
  };

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <View style={styles.container}>
      {/* Progress indicator */}
      <View style={styles.progressContainer}>
        <View
          style={[styles.progressBar, { width: `${scrollProgress * 100}%` }]}
        />
      </View>

      <ScrollView
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
        onScroll={handleScroll}
        scrollEventThrottle={16}
      >
        <Animated.View
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>{title}</Text>
            {estimated_duration && (
              <Text style={styles.duration}>
                Estimated reading time: {Math.ceil(estimated_duration / 60)} min
              </Text>
            )}
          </View>

          {/* Main content */}
          <Card style={styles.contentCard}>
            <Text style={styles.snippet}>{snippet}</Text>
          </Card>

          {/* Core concept */}
          {renderCoreConcept()}

          {/* Key points */}
          {renderKeyPoints()}

          {/* Examples */}
          {renderExamples()}

          {/* Reading progress feedback */}
          {hasStartedReading && (
            <Card style={styles.progressCard}>
              <Text style={styles.progressTitle}>Reading Progress</Text>
              <Text style={styles.progressText}>
                Time spent: {formatTime(timeSpent)}
              </Text>
              <View style={styles.progressIndicator}>
                <View
                  style={[
                    styles.progressFill,
                    { width: `${scrollProgress * 100}%` },
                  ]}
                />
              </View>
              {!canContinue && (
                <Text style={styles.progressHint}>
                  {scrollProgress < 0.8
                    ? 'Continue reading to unlock the next section'
                    : 'Almost done! Keep reading...'}
                </Text>
              )}
            </Card>
          )}
        </Animated.View>
      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <Button
          title={
            canContinue
              ? 'Continue'
              : `Continue (${Math.ceil((estimated_duration || 30) * 0.7 - timeSpent)}s)`
          }
          onPress={onContinue}
          loading={isLoading}
          disabled={!canContinue}
          style={[
            styles.continueButton,
            !canContinue && styles.continueButtonDisabled,
          ]}
        />
      </View>
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },
    progressContainer: {
      height: 3,
      backgroundColor: theme.colors?.border || '#E0E0E0',
    },
    progressBar: {
      height: '100%',
      backgroundColor: theme.colors?.primary || '#007AFF',
    },
    scrollContainer: {
      flex: 1,
    },
    content: {
      paddingBottom: theme.spacing?.xl || 24,
    },
    header: {
      padding: theme.spacing?.lg || 16,
      paddingBottom: theme.spacing?.md || 12,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors?.text || '#000000',
      textAlign: 'center',
      marginBottom: theme.spacing?.sm || 8,
    },
    duration: {
      fontSize: 14,
      color: theme.colors?.textSecondary || '#666666',
      textAlign: 'center',
    },
    contentCard: {
      margin: theme.spacing?.lg || 16,
      padding: theme.spacing?.lg || 16,
    },
    snippet: {
      fontSize: 16,
      lineHeight: 24,
      color: theme.colors?.text || '#000000',
    },
    conceptCard: {
      margin: theme.spacing?.lg || 16,
      padding: theme.spacing?.lg || 16,
      backgroundColor: theme.colors?.primaryLight || '#E3F2FD',
      borderLeftWidth: 4,
      borderLeftColor: theme.colors?.primary || '#007AFF',
    },
    conceptLabel: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.colors?.primary || '#007AFF',
      marginBottom: theme.spacing?.sm || 8,
      textTransform: 'uppercase',
      letterSpacing: 0.5,
    },
    conceptText: {
      fontSize: 16,
      lineHeight: 22,
      color: theme.colors?.text || '#000000',
      fontWeight: '500',
    },
    sectionCard: {
      margin: theme.spacing?.lg || 16,
      padding: theme.spacing?.lg || 16,
      backgroundColor: theme.colors?.surface || '#F8F9FA',
      borderRadius: 12,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: theme.colors?.text || '#000000',
      marginBottom: theme.spacing?.md || 12,
    },
    keyPointItem: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginBottom: theme.spacing?.md || 12,
    },
    keyPointBullet: {
      width: 6,
      height: 6,
      borderRadius: 3,
      backgroundColor: theme.colors?.primary || '#007AFF',
      marginTop: 8,
      marginRight: theme.spacing?.md || 12,
    },
    keyPointText: {
      flex: 1,
      fontSize: 15,
      lineHeight: 22,
      color: theme.colors?.text || '#000000',
    },
    exampleCard: {
      padding: theme.spacing?.md || 12,
      marginBottom: theme.spacing?.sm || 8,
      backgroundColor: theme.colors?.background || '#FFFFFF',
      borderWidth: 1,
      borderColor: theme.colors?.border || '#E0E0E0',
    },
    exampleText: {
      fontSize: 14,
      lineHeight: 20,
      color: theme.colors?.textSecondary || '#666666',
      fontStyle: 'italic',
    },
    progressCard: {
      margin: theme.spacing?.lg || 16,
      padding: theme.spacing?.lg || 16,
      backgroundColor: theme.colors?.successLight || '#E8F5E8',
      borderWidth: 1,
      borderColor: theme.colors?.success || '#4CAF50',
    },
    progressTitle: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors?.success || '#4CAF50',
      marginBottom: theme.spacing?.sm || 8,
    },
    progressText: {
      fontSize: 14,
      color: theme.colors?.text || '#000000',
      marginBottom: theme.spacing?.md || 12,
    },
    progressIndicator: {
      height: 8,
      backgroundColor: theme.colors?.border || '#E0E0E0',
      borderRadius: 4,
      overflow: 'hidden',
      marginBottom: theme.spacing?.sm || 8,
    },
    progressFill: {
      height: '100%',
      backgroundColor: theme.colors?.success || '#4CAF50',
    },
    progressHint: {
      fontSize: 12,
      color: theme.colors?.textSecondary || '#666666',
      fontStyle: 'italic',
    },
    footer: {
      padding: theme.spacing?.lg || 16,
      paddingTop: theme.spacing?.md || 12,
      backgroundColor: theme.colors?.surface || '#F8F9FA',
      borderTopWidth: 1,
      borderTopColor: theme.colors?.border || '#E0E0E0',
    },
    continueButton: {
      width: '100%',
    },
    continueButtonDisabled: {
      opacity: 0.6,
    },
  });
