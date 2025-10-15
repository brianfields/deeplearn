import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import type { LearningCoachBrief } from '../models';
import { uiSystemProvider } from '../../ui_system/public';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();
const primaryTextColor = uiSystem.isLightColor(theme.colors.primary)
  ? theme.colors.text
  : theme.colors.surface;

interface Props {
  readonly brief: LearningCoachBrief;
  readonly onAccept: () => void;
  readonly onIterate: () => void;
  readonly isAccepting: boolean;
}

export function BriefCard({ brief, onAccept, onIterate, isAccepting }: Props): React.ReactElement {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{brief.title}</Text>
      <Text style={styles.description}>{brief.description}</Text>
      <Text style={styles.subtitle}>Objectives</Text>
      {brief.objectives.map((objective, index) => (
        <Text key={`${objective}-${index}`} style={styles.objective}>
          • {objective}
        </Text>
      ))}
      {brief.notes ? (
        <Text style={styles.notes}>Coach Notes: {brief.notes}</Text>
      ) : null}
      <View style={styles.actions}>
        <Pressable
          style={({ pressed }) => [
            styles.secondaryButton,
            { opacity: pressed ? 0.6 : 1 },
          ]}
          onPress={onIterate}
          disabled={isAccepting}
        >
          <Text style={styles.secondaryText}>Ask for changes</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [
            styles.primaryButton,
            { opacity: pressed || isAccepting ? 0.6 : 1 },
          ]}
          onPress={onAccept}
          disabled={isAccepting}
        >
          <Text style={styles.primaryText}>{isAccepting ? 'Accepting…' : 'Accept brief'}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    margin: 16,
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: theme.colors.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 6,
  },
  objective: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: 4,
  },
  notes: {
    fontSize: 13,
    color: theme.colors.textSecondary ?? theme.colors.text,
    marginTop: 12,
  },
  actions: {
    flexDirection: 'row',
    marginTop: 16,
  },
  primaryButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 12,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
  },
  primaryText: {
    color: primaryTextColor,
    fontWeight: '600',
  },
  secondaryButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 12,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.border,
    marginRight: 12,
  },
  secondaryText: {
    color: theme.colors.text,
    fontWeight: '600',
  },
});
