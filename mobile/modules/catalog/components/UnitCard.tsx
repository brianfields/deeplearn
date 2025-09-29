import React from 'react';
import { View, StyleSheet, Image } from 'react-native';
import type { Unit } from '../../content/public';
import { UnitProgressIndicator } from './UnitProgressIndicator';
import {
  Card,
  Text,
  Box,
  Button,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';

interface Props {
  unit: Unit;
  onPress: (u: Unit) => void;
  onRetry?: (unitId: string) => void;
  onDismiss?: (unitId: string) => void;
  index?: number;
}

export function UnitCard({
  unit,
  onPress,
  onRetry,
  onDismiss,
  index,
}: Props): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { trigger } = useHaptics();

  const isDisabled = !unit.isInteractive;
  const showFailedActions: boolean =
    unit.status === 'failed' && !!(onRetry || onDismiss);
  const ownershipBadgeBackground = unit.isGlobal
    ? theme.colors.primary
    : theme.colors.surface;
  const ownershipBadgeTextColor = unit.isGlobal
    ? theme.colors.surface
    : theme.colors.textSecondary;

  const handlePress = (): void => {
    if (isDisabled) return;
    trigger('light');
    onPress(unit);
  };

  const handleRetry = (): void => {
    if (!onRetry) return;
    trigger('medium');
    onRetry(unit.id);
  };

  const handleDismiss = (): void => {
    if (!onDismiss) return;
    trigger('light');
    onDismiss(unit.id);
  };

  return (
    <Box
      testID={index !== undefined ? `unit-card-${index}` : undefined}
      mb="sm"
    >
      <Card
        variant="default"
        onPress={handlePress}
        disabled={isDisabled}
        style={[
          unit.status === 'failed'
            ? { borderLeftWidth: 4, borderLeftColor: theme.colors.error }
            : null,
        ]}
      >
        <View style={[styles.cardRow, { gap: ui.getSpacing('md') }]}>
          <View
            style={[
              styles.thumbnailShell,
              {
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.border,
              },
              ui.getDesignSystem().shadows.small as any,
            ]}
          >
            {unit.coverImageUrl ? (
              <Image
                source={{ uri: unit.coverImageUrl }}
                resizeMode="cover"
                style={styles.thumbnailImage}
                accessibilityRole="image"
                accessibilityLabel={`Cover art for ${unit.title}`}
              />
            ) : (
              <View
                style={[
                  styles.thumbnailPlaceholder,
                  { backgroundColor: theme.colors.border },
                ]}
              >
                <Text
                  variant="caption"
                  color={theme.colors.textSecondary}
                  style={{ textAlign: 'center' }}
                >
                  Visual preview incoming
                </Text>
              </View>
            )}
          </View>

          <View style={{ flex: 1 }}>
            {/* Header */}
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: ui.getSpacing('sm'),
              }}
            >
              <Text
                variant="title"
                weight="700"
                color={isDisabled ? theme.colors.textSecondary : theme.colors.text}
                style={{ flex: 1, marginRight: ui.getSpacing('sm') }}
                numberOfLines={2}
              >
                {unit.title}
              </Text>

              <View style={{ flexDirection: 'row', columnGap: 8 }}>
                <View
                  style={{
                    backgroundColor: ownershipBadgeBackground,
                    paddingHorizontal: 8,
                    paddingVertical: 4,
                    borderRadius: 8,
                    borderWidth: StyleSheet.hairlineWidth,
                    borderColor: theme.colors.border,
                  }}
                >
                  <Text
                    variant="caption"
                    color={ownershipBadgeTextColor}
                    weight="600"
                  >
                    {unit.ownershipLabel}
                  </Text>
                </View>
                <View
                  style={{
                    backgroundColor: isDisabled
                      ? theme.colors.border
                      : theme.colors.accent,
                    paddingHorizontal: 8,
                    paddingVertical: 4,
                    borderRadius: 8,
                  }}
                >
                  <Text
                    variant="caption"
                    color={
                      ui.isLightColor(theme.colors.accent)
                        ? theme.colors.surface
                        : theme.colors.background
                    }
                    weight="600"
                  >
                    {unit.difficultyLabel}
                  </Text>
                </View>
              </View>
            </View>

            {/* Description */}
            <Text
              variant="secondary"
              color={isDisabled ? theme.colors.textSecondary : undefined}
              numberOfLines={2}
              style={{ marginBottom: ui.getSpacing('sm') }}
            >
              {unit.description || unit.progressMessage}
            </Text>

            {/* Status indicator for non-completed units */}
            {unit.status !== 'completed' && (
              <View style={{ marginBottom: ui.getSpacing('sm') }}>
                <UnitProgressIndicator
                  status={unit.status}
                  progress={unit.creationProgress}
                  errorMessage={unit.errorMessage}
                />
              </View>
            )}

            {/* Failed unit actions */}
            {showFailedActions && (
              <View
                style={{
                  flexDirection: 'row',
                  justifyContent: 'flex-end',
                  marginTop: ui.getSpacing('sm'),
                  marginBottom: ui.getSpacing('xs'),
                  columnGap: ui.getSpacing('sm'),
                }}
              >
                {onRetry && (
                  <Button
                    title="Retry"
                    variant="primary"
                    size="small"
                    onPress={handleRetry}
                    testID={
                      index !== undefined ? `retry-button-${index}` : undefined
                    }
                  />
                )}
                {onDismiss && (
                  <Button
                    title="Dismiss"
                    variant="secondary"
                    size="small"
                    onPress={handleDismiss}
                    testID={
                      index !== undefined ? `dismiss-button-${index}` : undefined
                    }
                  />
                )}
              </View>
            )}

            {/* Footer */}
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text
                variant="caption"
                color={isDisabled ? theme.colors.textSecondary : undefined}
              >
                {unit.lessonCount} lessons
              </Text>
              {typeof unit.targetLessonCount === 'number' && (
                <Text
                  variant="caption"
                  color={isDisabled ? theme.colors.textSecondary : undefined}
                >
                  Target: {unit.targetLessonCount}
                </Text>
              )}
            </View>
          </View>
        </View>
      </Card>
    </Box>
  );
}

const styles = StyleSheet.create({
  cardRow: {
    flexDirection: 'row',
    alignItems: 'stretch',
  },
  thumbnailShell: {
    width: 96,
    height: 96,
    borderRadius: 24,
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center',
  },
  thumbnailImage: {
    width: '100%',
    height: '100%',
  },
  thumbnailPlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 12,
  },
});
