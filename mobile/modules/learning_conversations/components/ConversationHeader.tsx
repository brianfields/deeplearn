import React from 'react';
import { View, Pressable, Text, StyleSheet } from 'react-native';
import { uiSystemProvider } from '../../ui_system/public';

interface Props {
  readonly title: string;
  readonly onClose: () => void;
  readonly subtitle?: string;
}

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

/**
 * ConversationHeader is a shared header component for all conversation types.
 *
 * Ensures consistent appearance across Learning Coach and Teaching Assistant:
 * - Unified title styling
 * - Consistent close button affordance (✕)
 * - Optional subtitle for context
 *
 * This component is used by both full-screen (LearningCoachScreen) and
 * modal (TeachingAssistantModal) implementations to ensure visual consistency.
 */
export function ConversationHeader({
  title,
  onClose,
  subtitle,
}: Props): React.ReactElement {
  return (
    <View>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.title} numberOfLines={2} ellipsizeMode="tail">
            {title}
          </Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Close ${title}`}
          onPress={onClose}
          style={({ pressed }) => [
            styles.closeButton,
            pressed && styles.closePressed,
          ]}
        >
          <Text style={styles.closeText}>✕</Text>
        </Pressable>
      </View>
      {subtitle ? (
        <View style={styles.subtitleContainer}>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border ?? 'rgba(0,0,0,0.1)',
  },
  titleContainer: {
    flex: 1,
    marginRight: 8,
  },
  title: {
    fontSize: 17,
    fontWeight: '600',
    color: theme.colors.text,
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
  },
  closePressed: {
    opacity: 0.6,
  },
  closeText: {
    fontSize: 24,
    fontWeight: '600',
    color: theme.colors.text,
  },
  subtitleContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  subtitle: {
    fontSize: 13,
    color: theme.colors.textSecondary ?? '#666',
    lineHeight: 18,
  },
});
