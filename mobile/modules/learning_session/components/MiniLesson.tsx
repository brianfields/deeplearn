/**
 * MiniLesson Component - Educational Content Presentation
 *
 * This component presents educational content in an engaging, mobile-optimized format.
 * It's designed to deliver knowledge before testing understanding, serving as the
 * "teaching" phase of the learning experience.
 *
 * Renamed from DidacticSnippet to MiniLesson per new model terminology.
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
  Easing,
} from 'react-native-reanimated';

// Icons
import {
  Target,
  ChevronRight,
  CheckCircle,
  Lightbulb,
} from 'lucide-react-native';

// Components
import { Button, Card, useHaptics } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import { reducedMotion } from '../../ui_system/utils/motion';
import { animationTimings } from '../../ui_system/utils/animations';

interface MiniLessonProps {
  snippet: {
    title?: string;
    snippet?: string;
    explanation?: string;
    key_points?: string[];
    examples?: string[];
    estimated_duration?: number;
  };
  onContinue: () => void;
  isLoading?: boolean;
}

export default function MiniLesson({
  snippet,
  onContinue,
  isLoading = false,
}: MiniLessonProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);
  const haptics = useHaptics();

  const [hasScrolled, setHasScrolled] = useState(false);

  console.log('📖 [MiniLesson] Received snippet:', snippet);

  // Animated values
  const continueButtonOpacity = useSharedValue(0);

  const handleScroll = (event: any) => {
    const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
    const isScrolledToBottom =
      contentOffset.y + layoutMeasurement.height >= contentSize.height - 50;

    if (isScrolledToBottom && !hasScrolled) {
      setHasScrolled(true);
      if (reducedMotion.enabled) {
        continueButtonOpacity.value = 1;
      } else {
        continueButtonOpacity.value = withSpring(1, {
          damping: 15,
          stiffness: 150,
        });
      }
    }
  };

  const continueButtonStyle = useAnimatedStyle(() => ({
    opacity: continueButtonOpacity.value,
    transform: [
      {
        translateY: reducedMotion.enabled
          ? 0
          : withTiming(hasScrolled ? 0 : 20),
      },
    ],
  }));

  // Show continue button after short delay if content is short
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (!hasScrolled) {
        setHasScrolled(true);
        continueButtonOpacity.value = reducedMotion.enabled ? 1 : withSpring(1);
      }
    }, 3000); // Show after 3 seconds even if not scrolled

    return () => clearTimeout(timer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Ensure we have valid content structure
  if (!snippet) {
    console.error('MiniLesson: No snippet provided');
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>No content available</Text>
        </View>
      </View>
    );
  }

  // Extract content with fallbacks
  const title = snippet.title || 'Learning Lesson';
  const content =
    snippet.explanation || snippet.snippet || 'Content will be displayed here.';
  const key_points = snippet.key_points || [];
  const examples = snippet.examples || [];

  return (
    <View style={styles.container}>
      {/* Main Content */}
      <Animated.View
        entering={
          reducedMotion.enabled
            ? undefined
            : SlideInUp.delay(200)
                .duration(animationTimings.ui)
                .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
        }
        style={styles.contentContainer}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          showsVerticalScrollIndicator={false}
          testID="didactic-content-scroll"
        >
          {/* Main Content */}
          <View style={styles.contentSection}>
            <Text style={styles.contentText}>{content}</Text>
          </View>

          {/* Key Points Section */}
          {key_points && key_points.length > 0 && (
            <Animated.View
              entering={
                reducedMotion.enabled
                  ? undefined
                  : FadeIn.delay(400)
                      .duration(animationTimings.ui)
                      .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
              }
              style={styles.keyPointsSection}
            >
              <View style={styles.keyPointsHeader}>
                <Target size={20} color={theme.colors.secondary} />
                <Text style={styles.keyPointsTitle}>Key Points</Text>
              </View>

              <Card style={styles.keyPointsCard}>
                {key_points.map((point, index) => (
                  <Animated.View
                    key={index}
                    entering={
                      reducedMotion.enabled
                        ? undefined
                        : FadeIn.delay(500 + index * animationTimings.stagger)
                            .duration(animationTimings.ui)
                            .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
                    }
                    style={styles.keyPointItem}
                  >
                    <View style={styles.keyPointBullet}>
                      <CheckCircle size={16} color={theme.colors.secondary} />
                    </View>
                    <Text style={styles.keyPointText}>{point}</Text>
                  </Animated.View>
                ))}
              </Card>
            </Animated.View>
          )}

          {/* Examples Section */}
          {examples && examples.length > 0 && (
            <Animated.View
              entering={
                reducedMotion.enabled
                  ? undefined
                  : FadeIn.delay(600)
                      .duration(animationTimings.ui)
                      .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
              }
              style={styles.examplesSection}
            >
              <View style={styles.examplesHeader}>
                <Lightbulb size={20} color={theme.colors.warning} />
                <Text style={styles.examplesTitle}>Examples</Text>
              </View>

              <Card style={styles.examplesCard}>
                {examples.map((example, index) => (
                  <Animated.View
                    key={index}
                    entering={
                      reducedMotion.enabled
                        ? undefined
                        : FadeIn.delay(700 + index * animationTimings.stagger)
                            .duration(animationTimings.ui)
                            .easing(Easing.bezier(0.2, 0.8, 0.2, 1))
                    }
                    style={[
                      styles.exampleItem,
                      index !== examples.length - 1 && styles.exampleItemBorder,
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
          onPress={() => {
            haptics.trigger('medium');
            onContinue();
          }}
          loading={isLoading}
          size="large"
          style={styles.continueButton}
          testID="didactic-continue-button"
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
              color={theme.colors.textSecondary}
              style={{ transform: [{ rotate: '90deg' }] }}
            />
          </Animated.View>
        </Animated.View>
      )}
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },

    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
    },

    errorText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },

    titleSection: {
      paddingTop: 20,
      paddingHorizontal: 20,
      paddingBottom: 16,
    },

    title: {
      ...theme.typography?.heading2,
      color: theme.colors.text,
      marginBottom: 8,
      fontWeight: 'normal',
    },

    subtitle: {
      ...theme.typography?.body,
      color: theme.colors.textSecondary,
    },

    contentContainer: {
      flex: 1,
    },

    scrollView: {
      flex: 1,
    },

    scrollContent: {
      padding: 20,
      paddingBottom: 160, // Extra space for continue button
    },

    contentSection: {
      marginBottom: 24,
    },

    contentText: {
      ...theme.typography?.body,
      color: theme.colors.text,
    },

    keyPointsSection: {
      marginBottom: 20,
    },

    keyPointsHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 16,
    },

    keyPointsTitle: {
      ...theme.typography?.heading3,
      color: theme.colors.text,
      marginLeft: 12,
    },

    keyPointsCard: {
      paddingVertical: 12,
    },

    keyPointItem: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginBottom: 12,
    },

    keyPointBullet: {
      marginRight: 12,
      marginTop: 2, // Align with text
    },

    keyPointText: {
      ...theme.typography?.body,
      color: theme.colors.text,
      flex: 1,
    },

    examplesSection: {
      marginBottom: 20,
    },

    examplesHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 16,
    },

    examplesTitle: {
      ...theme.typography?.heading3,
      color: theme.colors.text,
      marginLeft: 12,
      fontWeight: 'normal',
    },

    examplesCard: {
      paddingVertical: 12,
    },

    exampleItem: {
      paddingVertical: 12,
    },

    exampleItemBorder: {
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },

    exampleText: {
      ...theme.typography?.body,
      color: theme.colors.text,
      fontStyle: 'italic',
    },

    bottomSpacing: {
      height: 40,
    },

    continueButtonContainer: {
      position: 'absolute',
      bottom: 20,
      left: 20,
      right: 20,
    },

    continueButton: {},

    scrollIndicator: {
      position: 'absolute',
      bottom: 80,
      right: 20,
      alignItems: 'center',
    },

    scrollIndicatorText: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginBottom: 8,
    },

    scrollArrow: {
      padding: 8,
    },
  });
