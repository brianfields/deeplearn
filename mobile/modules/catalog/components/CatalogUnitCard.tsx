import React from 'react';
import { View } from 'react-native';
import { Check, Plus, Trash2 } from 'lucide-react-native';
import type { Unit } from '../../content/public';
import {
  Box,
  Card,
  Text,
  Button,
  ArtworkImage,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { layoutStyles } from '../../ui_system/styles/layout';

interface CatalogUnitCardProps {
  readonly unit: Unit;
  readonly isInMyUnits: boolean;
  readonly onAdd: (unit: Unit) => void;
  readonly onRemove: (unit: Unit) => void;
  readonly isActionPending?: boolean;
  readonly disabled?: boolean;
  readonly index?: number;
}

export function CatalogUnitCard({
  unit,
  isInMyUnits,
  onAdd,
  onRemove,
  isActionPending = false,
  disabled = false,
  index,
}: CatalogUnitCardProps): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { trigger } = useHaptics();

  const handleAdd = (): void => {
    if (disabled || isActionPending) {
      return;
    }
    trigger('medium');
    onAdd(unit);
  };

  const handleRemove = (): void => {
    if (disabled || isActionPending) {
      return;
    }
    trigger('light');
    onRemove(unit);
  };

  const titleColor = disabled ? theme.colors.textSecondary : theme.colors.text;

  const descriptionColor = disabled
    ? theme.colors.textSecondary
    : theme.colors.textSecondary;

  const actionButton = isInMyUnits ? (
    <Button
      title="Remove from My Units"
      variant="destructive"
      size="small"
      onPress={handleRemove}
      loading={isActionPending}
      disabled={disabled}
      icon={<Trash2 size={16} color={theme.colors.surface} />}
      testID={
        index !== undefined
          ? `catalog-unit-remove-button-${index}`
          : 'catalog-unit-remove-button'
      }
    />
  ) : (
    <Button
      title="Add to My Units"
      variant="primary"
      size="small"
      onPress={handleAdd}
      loading={isActionPending}
      disabled={disabled}
      icon={<Plus size={16} color={theme.colors.surface} />}
      testID={
        index !== undefined
          ? `catalog-unit-add-button-${index}`
          : 'catalog-unit-add-button'
      }
    />
  );

  return (
    <Box
      mb="sm"
      testID={
        index !== undefined ? `catalog-unit-card-${index}` : 'catalog-unit-card'
      }
    >
      <Card variant="default" disabled={disabled}>
        <View
          style={[layoutStyles.rowStart, { columnGap: ui.getSpacing('md') }]}
        >
          <ArtworkImage
            title={unit.title}
            imageUrl={unit.artImageUrl ?? undefined}
            description={unit.artImageDescription ?? undefined}
            variant="thumbnail"
            style={layoutStyles.flexShrink0}
            testID={
              index !== undefined
                ? `catalog-unit-art-${index}`
                : 'catalog-unit-art'
            }
          />
          <View style={layoutStyles.flex1}>
            <View
              style={[
                layoutStyles.rowBetweenStart,
                { marginBottom: ui.getSpacing('sm') },
              ]}
            >
              <Text
                variant="title"
                weight="700"
                color={titleColor}
                numberOfLines={2}
                style={[
                  layoutStyles.flex1,
                  { marginRight: ui.getSpacing('sm') },
                ]}
              >
                {unit.title}
              </Text>
              {isInMyUnits ? (
                <View
                  style={[
                    layoutStyles.row,
                    {
                      paddingHorizontal: ui.getSpacing('xs'),
                      paddingVertical: ui.getSpacing('xs'),
                      backgroundColor: theme.colors.success,
                    },
                    layoutStyles.radiusRound,
                  ]}
                  testID={
                    index !== undefined
                      ? `catalog-unit-badge-${index}`
                      : 'catalog-unit-badge'
                  }
                >
                  <Check
                    size={14}
                    color={theme.colors.surface}
                    style={{ marginRight: ui.getSpacing('xs') }}
                  />
                  <Text
                    variant="caption"
                    color={theme.colors.surface}
                    weight="600"
                  >
                    In My Units
                  </Text>
                </View>
              ) : null}
            </View>

            {unit.description ? (
              <Text
                variant="secondary"
                color={descriptionColor}
                numberOfLines={3}
                style={{ marginBottom: ui.getSpacing('sm') }}
              >
                {unit.description}
              </Text>
            ) : null}

            <View
              style={[
                layoutStyles.rowBetween,
                { marginTop: ui.getSpacing('sm') },
              ]}
            >
              <Text variant="caption" color={theme.colors.textSecondary}>
                {unit.lessonCount} lessons
              </Text>
              {actionButton}
            </View>
          </View>
        </View>
      </Card>
    </Box>
  );
}
