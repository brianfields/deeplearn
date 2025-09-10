/**
 * DidacticSnippet Component - Educational Content Presentation
 *
 * This component presents educational content in an engaging, mobile-optimized format.
 * It's designed to deliver knowledge before testing understanding, serving as the
 * "teaching" phase of the learning experience.
 *
 * Based on the original DidacticSnippet component, adapted for the new modular architecture.
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
  Target,
  ChevronRight,
  CheckCircle,
  Lightbulb,
} from 'lucide-react-native';

// Components
import { Button, Card } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';

interface DidacticSnippetProps {
  snippet: {
    title?: string;
    core_concept?: string;
    snippet?: string;
    explanation?: string;
    key_points?: string[];
    examples?: string[];
    estimated_duration?: number;
  };
  onContinue: () => void;
  isLoading?: boolean;
}

export default function DidacticSnippet({
  snippet,
  onContinue,
  isLoading = false,
}: DidacticSnippetProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

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

  // Extract content with fallbacks
  const title = snippet.title || 'Learning Lesson';
  const content =
    snippet.explanation || snippet.snippet || 'Content will be displayed here.';
  const core_concept = snippet.core_concept;
  const key_points = snippet.key_points || [];
  const examples = snippet.examples || [];

  return (
    <View style={styles.container}>
      {/* Clean Title */}
      <Animated.View entering={FadeIn} style={styles.titleSection}>
        <Text style={styles.title}>{title}</Text>
        {core_concept && <Text style={styles.subtitle}>{core_concept}</Text>}
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
          {/* Main Content */}
          <View style={styles.contentSection}>
            <Text style={styles.contentText}>{content}</Text>
          </View>

          {/* Key Points Section */}
          {key_points && key_points.length > 0 && (
            <Animated.View
              entering={FadeIn.delay(400)}
              style={styles.keyPointsSection}
            >
              <View style={styles.keyPointsHeader}>
                <Target
                  size={20}
                  color={theme.colors?.secondary || '#007AFF'}
                />
                <Text style={styles.keyPointsTitle}>Key Points</Text>
              </View>

              <Card style={styles.keyPointsCard}>
                {key_points.map((point, index) => (
                  <Animated.View
                    key={index}
                    entering={FadeIn.delay(500 + index * 100)}
                    style={styles.keyPointItem}
                  >
                    <View style={styles.keyPointBullet}>
                      <CheckCircle
                        size={16}
                        color={theme.colors?.secondary || '#007AFF'}
                      />
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
              entering={FadeIn.delay(600)}
              style={styles.examplesSection}
            >
              <View style={styles.examplesHeader}>
                <Lightbulb
                  size={20}
                  color={theme.colors?.warning || '#FF9500'}
                />
                <Text style={styles.examplesTitle}>Examples</Text>
              </View>

              <Card style={styles.examplesCard}>
                {examples.map((example, index) => (
                  <Animated.View
                    key={index}
                    entering={FadeIn.delay(700 + index * 100)}
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
          onPress={onContinue}
          loading={isLoading}
          size="large"
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
              color={theme.colors?.textSecondary || '#666666'}
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
      backgroundColor: theme.colors?.background || '#FFFFFF',
    },

    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
    },

    errorText: {
      fontSize: 16,
      color: theme.colors?.textSecondary || '#666666',
      textAlign: 'center',
    },

    titleSection: {
      paddingTop: 20,
      paddingHorizontal: 20,
      paddingBottom: 16,
    },

    title: {
      fontSize: 28,
      fontWeight: '700' as const,
      lineHeight: 34,
      color: theme.colors?.text || '#000000',
      marginBottom: 8,
    },

    subtitle: {
      fontSize: 17,
      fontWeight: '400' as const,
      lineHeight: 22,
      color: theme.colors?.textSecondary || '#666666',
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
      fontSize: 17,
      fontWeight: '400' as const,
      lineHeight: 28,
      color: theme.colors?.text || '#000000',
      letterSpacing: -0.24,
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
      fontSize: 20,
      fontWeight: '600' as const,
      color: theme.colors?.text || '#000000',
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
      fontSize: 16,
      fontWeight: '400' as const,
      color: theme.colors?.text || '#000000',
      flex: 1,
      lineHeight: 24,
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
      fontSize: 20,
      fontWeight: '600' as const,
      color: theme.colors?.text || '#000000',
      marginLeft: 12,
    },

    examplesCard: {
      paddingVertical: 12,
    },

    exampleItem: {
      paddingVertical: 12,
    },

    exampleItemBorder: {
      borderBottomWidth: 1,
      borderBottomColor: theme.colors?.border || '#E5E5E7',
    },

    exampleText: {
      fontSize: 16,
      fontWeight: '400' as const,
      color: theme.colors?.text || '#000000',
      fontStyle: 'italic',
      lineHeight: 24,
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

    continueButton: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 4,
      },
      shadowOpacity: 0.3,
      shadowRadius: 4.65,
      elevation: 8,
    },

    scrollIndicator: {
      position: 'absolute',
      bottom: 80,
      right: 20,
      alignItems: 'center',
    },

    scrollIndicatorText: {
      fontSize: 12,
      color: theme.colors?.textSecondary || '#666666',
      marginBottom: 8,
    },

    scrollArrow: {
      padding: 8,
    },
  });
