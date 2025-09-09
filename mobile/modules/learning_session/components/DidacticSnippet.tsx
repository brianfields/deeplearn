/**
 * DidacticSnippet Component - Educational Content Presentation
 *
 * Presents educational content in an engaging, mobile-optimized format.
 * Serves as the "teaching" phase of the learning experience.
 *
 * This is a simplified version for the modular architecture.
 * Full implementation will be completed during Phase 3 integration.
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Button, Card } from '../../ui_system/public';
import { uiSystemProvider } from '../../ui_system/public';
import type { ComponentState } from '../models';

interface DidacticSnippetProps {
  component: ComponentState;
  onContinue: () => void;
  isLoading?: boolean;
}

export default function DidacticSnippet({
  component,
  onContinue,
  isLoading = false,
}: DidacticSnippetProps) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = createStyles(theme);

  // Extract content from component
  const content = component.content || {};
  const title = content.title || component.title || 'Educational Content';
  const snippet = content.snippet || 'Content will be displayed here.';

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>{title}</Text>
        </View>

        <Card style={styles.contentCard}>
          <Text style={styles.content}>{snippet}</Text>
        </Card>

        <Text style={styles.placeholder}>
          🚧 Didactic Snippet Component
          {'\n\n'}
          This component will present educational content with:
          {'\n'}• Rich text formatting
          {'\n'}• Key points highlighting
          {'\n'}• Examples and illustrations
          {'\n'}• Progress tracking
          {'\n\n'}
          Full implementation pending Phase 3 integration.
        </Text>
      </ScrollView>

      <View style={styles.footer}>
        <Button
          title="Continue"
          onPress={onContinue}
          loading={isLoading}
          style={styles.continueButton}
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
    scrollContainer: {
      flex: 1,
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
    },
    contentCard: {
      margin: theme.spacing?.lg || 16,
      padding: theme.spacing?.lg || 16,
    },
    content: {
      fontSize: 16,
      lineHeight: 24,
      color: theme.colors?.text || '#000000',
    },
    placeholder: {
      fontSize: 14,
      color: theme.colors?.textSecondary || '#666666',
      textAlign: 'center',
      margin: theme.spacing?.lg || 16,
      lineHeight: 20,
    },
    footer: {
      padding: theme.spacing?.lg || 16,
      paddingTop: theme.spacing?.md || 12,
    },
    continueButton: {
      width: '100%',
    },
  });
