import React from 'react';
import { StyleSheet, View } from 'react-native';
import NativeSlider from '@react-native-community/slider';
import { internalUiSystemProvider } from '../internalProvider';
import type { SliderProps } from '../models';
import { Text } from './primitives/Text';

const uiSystemProvider = internalUiSystemProvider;

export function Slider({
  value,
  minimumValue = 0,
  maximumValue,
  step,
  onValueChange,
  onSlidingStart,
  onSlidingComplete,
  disabled = false,
  minimumTrackTintColor,
  maximumTrackTintColor,
  thumbTintColor,
  showValueLabels = false,
  formatValueLabel,
  minimumLabel,
  maximumLabel,
  containerStyle,
  sliderStyle,
  testID,
}: SliderProps): React.ReactElement {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const labelSpacing = uiSystem.getSpacing('xs');

  const resolvedMinTrack = minimumTrackTintColor ?? theme.colors.primary;
  const resolvedMaxTrack = maximumTrackTintColor ?? theme.colors.border;
  const resolvedThumb = thumbTintColor ?? theme.colors.primary;

  const formatLabel = (val: number): string => {
    if (!Number.isFinite(val)) {
      return '0';
    }

    if (formatValueLabel) {
      return formatValueLabel(val);
    }

    return `${Math.round(val)}`;
  };

  const effectiveMinLabel =
    minimumLabel ?? formatLabel(minimumValue ?? 0);
  const effectiveMaxLabel = maximumLabel ?? formatLabel(maximumValue);
  const effectiveValueLabel = formatLabel(value);

  return (
    <View style={StyleSheet.flatten([styles.container, containerStyle])}>
      <NativeSlider
        value={Number.isFinite(value) ? value : 0}
        minimumValue={minimumValue}
        maximumValue={maximumValue}
        step={step}
        disabled={disabled}
        onValueChange={onValueChange}
        onSlidingStart={onSlidingStart}
        onSlidingComplete={onSlidingComplete}
        minimumTrackTintColor={resolvedMinTrack}
        maximumTrackTintColor={resolvedMaxTrack}
        thumbTintColor={resolvedThumb}
        style={StyleSheet.flatten([styles.slider, sliderStyle])}
        tapToSeek
        testID={testID}
      />
      {showValueLabels && (
        <View style={[styles.labelsRow, { marginTop: labelSpacing }]}> 
          <Text variant="caption">{effectiveValueLabel}</Text>
          <Text variant="caption">{effectiveMaxLabel}</Text>
        </View>
      )}
      {!showValueLabels && (minimumLabel || maximumLabel) && (
        <View style={[styles.labelsRow, { marginTop: labelSpacing }]}> 
          <Text variant="caption">{effectiveMinLabel}</Text>
          <Text variant="caption">{effectiveMaxLabel}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  labelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});

export default Slider;
