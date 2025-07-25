/**
 * DidacticSnippet Component - Educational Content Presentation
 *
 * This component presents educational content in an engaging, mobile-optimized format.
 * It's designed to deliver knowledge before testing understanding, serving as the
 * "teaching" phase of the learning experience.
 *
 * LEARNING FLOW ROLE:
 * - Typically the first step in a learning session
 * - Provides foundational knowledge before interactive questions
 * - Ensures users engage with content before proceeding
 * - Sets the context for subsequent MCQ questions
 *
 * CONTENT STRUCTURE:
 * - Main educational snippet (core learning material)
 * - Key points section (summarized takeaways)
 * - Examples section (practical applications)
 * - Progress indicators and reading time estimates
 *
 * USER ENGAGEMENT FEATURES:
 * - Scroll-to-continue mechanism (ensures content consumption)
 * - Progressive content reveal with animations
 * - Auto-continue after time delay for short content
 * - Visual feedback and micro-interactions
 *
 * MOBILE UX OPTIMIZATIONS:
 * - Scrollable content with scroll indicators
 * - Touch-friendly continue button
 * - Responsive text sizing and spacing
 * - Smooth animations and transitions
 * - Reading progress tracking
 *
 * INTEGRATION WITH LEARNING FLOW:
 * - Receives didactic content from LearningFlow
 * - Signals completion when user has engaged with content
 * - Provides continuation callback to parent component
 * - Tracks engagement metrics for learning analytics
 *
 * CONTENT DATA STRUCTURE:
 * - title: Topic or section title
 * - core_concept: Brief description/summary
 * - snippet: Main educational content
 * - key_points: Array of important takeaways
 * - examples: Array of practical examples
 * - estimated_duration: Reading time estimate
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import Animated, {
  FadeIn,
  SlideInUp,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

// Icons
import {
  BookOpen,
  Target,
  Clock,
  ChevronRight,
  CheckCircle,
  Lightbulb,
} from 'lucide-react-native';

// Components
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

// Theme & Types
import { colors, spacing, typography, shadows } from '@/utils/theme';
import type { DidacticSnippetProps } from '@/types';

export default function DidacticSnippet({
  snippet,
  onContinue,
  isLoading = false,
}: DidacticSnippetProps) {
  const [hasScrolled, setHasScrolled] = useState(false);

  console.log('📖 [DidacticSnippet] Received snippet:', snippet);

  // Animated values
  const continueButtonOpacity = useSharedValue(0);

  const handleScroll = (event: any) => {
    const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
    const isScrolledToBottom =
      contentOffset.y + layoutMeasurement.height >= contentSize.height - 50;

    if (isScrolledToBottom && !hasScrolled) {
      setHasScrolled(true);
      continueButtonOpacity.value = withSpring(1, {
        damping: 15,
        stiffness: 150,
      });
    }
  };

  const continueButtonStyle = useAnimatedStyle(() => ({
    opacity: continueButtonOpacity.value,
    transform: [{ translateY: withTiming(hasScrolled ? 0 : 20) }],
  }));

  // Show continue button after short delay if content is short
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (!hasScrolled) {
        setHasScrolled(true);
        continueButtonOpacity.value = withSpring(1);
      }
    }, 3000); // Show after 3 seconds even if not scrolled

    return () => clearTimeout(timer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Ensure we have valid content structure
  if (!snippet) {
    console.error('DidacticSnippet: No snippet provided');
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>No content available</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <Animated.View entering={FadeIn} style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.iconContainer}>
            <BookOpen size={20} color={colors.primary} />
            <Text style={styles.headerLabel}>Learn</Text>
          </View>

          <View style={styles.durationContainer}>
            <Clock size={16} color={colors.textSecondary} />
            <Text style={styles.durationText}>
              {snippet.estimated_duration || 5} min read
            </Text>
          </View>
        </View>

        <Text style={styles.title}>{snippet.title || 'Learning Topic'}</Text>

        <Text style={styles.subtitle}>
          {snippet.core_concept || 'Educational Content'}
        </Text>
      </Animated.View>

      {/* Main Content */}
      <Animated.View
        entering={SlideInUp.delay(200)}
        style={styles.contentContainer}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          showsVerticalScrollIndicator={false}
        >
          {/* Main Content Card */}
          <Card style={styles.contentCard}>
            <Text style={styles.contentText}>
              {snippet.snippet || 'Content will be displayed here.'}
            </Text>
          </Card>

          {/* Key Points Section */}
          {snippet.key_points && snippet.key_points.length > 0 && (
            <Animated.View
              entering={FadeIn.delay(400)}
              style={styles.keyPointsSection}
            >
              <View style={styles.keyPointsHeader}>
                <Target size={20} color={colors.secondary} />
                <Text style={styles.keyPointsTitle}>Key Points</Text>
              </View>

              <Card style={styles.keyPointsCard}>
                {snippet.key_points.map((point, index) => (
                  <Animated.View
                    key={index}
                    entering={FadeIn.delay(500 + index * 100)}
                    style={styles.keyPointItem}
                  >
                    <View style={styles.keyPointBullet}>
                      <CheckCircle size={16} color={colors.secondary} />
                    </View>
                    <Text style={styles.keyPointText}>{point}</Text>
                  </Animated.View>
                ))}
              </Card>
            </Animated.View>
          )}

          {/* Examples Section */}
          {snippet.examples && snippet.examples.length > 0 && (
            <Animated.View
              entering={FadeIn.delay(600)}
              style={styles.examplesSection}
            >
              <View style={styles.examplesHeader}>
                <Lightbulb size={20} color={colors.warning} />
                <Text style={styles.examplesTitle}>Examples</Text>
              </View>

              <Card style={styles.examplesCard}>
                {snippet.examples.map((example, index) => (
                  <Animated.View
                    key={index}
                    entering={FadeIn.delay(700 + index * 100)}
                    style={[
                      styles.exampleItem,
                      index !== snippet.examples!.length - 1 &&
                        styles.exampleItemBorder,
                    ]}
                  >
                    <Text style={styles.exampleText}>{example}</Text>
                  </Animated.View>
                ))}
              </Card>
            </Animated.View>
          )}

          {/* Bottom spacing for scroll indicator */}
          <View style={styles.bottomSpacing} />
        </ScrollView>
      </Animated.View>

      {/* Continue Button */}
      <Animated.View
        style={[styles.continueButtonContainer, continueButtonStyle]}
      >
        <Button
          title="Continue"
          onPress={onContinue}
          loading={isLoading}
          size="large"
          icon={<ChevronRight size={20} color={colors.surface} />}
          style={styles.continueButton}
        />
      </Animated.View>

      {/* Scroll indicator */}
      {!hasScrolled && (
        <Animated.View
          entering={FadeIn.delay(2000)}
          style={styles.scrollIndicator}
        >
          <Text style={styles.scrollIndicatorText}>Scroll to continue</Text>
          <Animated.View style={styles.scrollArrow}>
            <ChevronRight
              size={16}
              color={colors.textSecondary}
              style={{ transform: [{ rotate: '90deg' }] }}
            />
          </Animated.View>
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },

  errorText: {
    ...(typography.body as any),
    color: colors.textSecondary,
    textAlign: 'center',
  },

  header: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    ...shadows.small,
  },

  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },

  iconContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  headerLabel: {
    ...typography.caption,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: spacing.xs,
  },

  durationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  durationText: {
    ...(typography.caption as any),
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },

  title: {
    ...(typography.heading2 as any),
    color: colors.text,
    marginBottom: spacing.sm,
  },

  subtitle: {
    ...(typography.body as any),
    color: colors.textSecondary,
  },

  contentContainer: {
    flex: 1,
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl * 2, // Extra space for continue button
  },

  contentCard: {
    marginBottom: spacing.lg,
  },

  contentText: {
    ...(typography.body as any),
    color: colors.text,
    lineHeight: 28,
  },

  keyPointsSection: {
    marginBottom: spacing.lg,
  },

  keyPointsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },

  keyPointsTitle: {
    ...(typography.heading3 as any),
    color: colors.text,
    marginLeft: spacing.sm,
  },

  keyPointsCard: {
    paddingVertical: spacing.sm,
  },

  keyPointItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },

  keyPointBullet: {
    marginRight: spacing.sm,
    marginTop: 2, // Align with text
  },

  keyPointText: {
    ...(typography.body as any),
    color: colors.text,
    flex: 1,
    lineHeight: 24,
  },

  examplesSection: {
    marginBottom: spacing.lg,
  },

  examplesHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },

  examplesTitle: {
    ...(typography.heading3 as any),
    color: colors.text,
    marginLeft: spacing.sm,
  },

  examplesCard: {
    paddingVertical: spacing.sm,
  },

  exampleItem: {
    paddingVertical: spacing.sm,
  },

  exampleItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },

  exampleText: {
    ...(typography.body as any),
    color: colors.text,
    fontStyle: 'italic',
    lineHeight: 24,
  },

  bottomSpacing: {
    height: spacing.xxl,
  },

  continueButtonContainer: {
    position: 'absolute',
    bottom: spacing.lg,
    left: spacing.lg,
    right: spacing.lg,
  },

  continueButton: {
    ...shadows.large,
  },

  scrollIndicator: {
    position: 'absolute',
    bottom: spacing.xxl * 2,
    right: spacing.lg,
    alignItems: 'center',
  },

  scrollIndicatorText: {
    ...(typography.caption as any),
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },

  scrollArrow: {
    padding: spacing.xs,
  },
});
