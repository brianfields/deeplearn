import React from 'react';
import { View } from 'react-native';
import type { Unit } from '../../content/public';
import { UnitProgressIndicator } from './UnitProgressIndicator';
import {
  Card,
  Text,
  Box,
  Button,
  ArtworkImage,
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
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'flex-start',
            columnGap: ui.getSpacing('md'),
          }}
        >
          <ArtworkImage
            title={unit.title}
            imageUrl={unit.artImageUrl ?? undefined}
            description={unit.artImageDescription ?? undefined}
            variant="thumbnail"
            style={{ flexShrink: 0 }}
            testID={index !== undefined ? `unit-art-${index}` : undefined}
          />

          <View style={{ flex: 1 }}>
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                marginBottom: ui.getSpacing('sm'),
              }}
            >
              <Text
                variant="title"
                weight="700"
                color={
                  isDisabled ? theme.colors.textSecondary : theme.colors.text
                }
                style={{ flex: 1, marginRight: ui.getSpacing('sm') }}
                numberOfLines={2}
              >
                {unit.title}
              </Text>
            </View>

            <Text
              variant="secondary"
              color={isDisabled ? theme.colors.textSecondary : undefined}
              numberOfLines={2}
              style={{ marginBottom: ui.getSpacing('sm') }}
            >
              {unit.description || unit.progressMessage}
            </Text>

            {unit.status !== 'completed' && (
              <View style={{ marginBottom: ui.getSpacing('sm') }}>
                <UnitProgressIndicator
                  status={unit.status}
                  progress={unit.creationProgress}
                  errorMessage={unit.errorMessage}
                />
              </View>
            )}

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
                      index !== undefined
                        ? `dismiss-button-${index}`
                        : undefined
                    }
                  />
                )}
              </View>
            )}

            <View
              style={{ flexDirection: 'row', justifyContent: 'space-between' }}
            >
              <Text
                variant="caption"
                color={isDisabled ? theme.colors.textSecondary : undefined}
              >
                {unit.targetLessonCount} lessons
              </Text>
            </View>
          </View>
        </View>
      </Card>
    </Box>
  );
}
