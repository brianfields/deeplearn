import React from 'react';
import { View, ViewStyle } from 'react-native';
import { uiSystemProvider } from '../../public';
import type { Spacing } from '../../models';

export type BoxProps = {
  children?: React.ReactNode;
  style?: ViewStyle | ViewStyle[] | undefined;
  testID?: string;
  // Spacing shorthands using theme spacing scale or raw number
  p?: keyof Spacing | number;
  px?: keyof Spacing | number;
  py?: keyof Spacing | number;
  pt?: keyof Spacing | number;
  pr?: keyof Spacing | number;
  pb?: keyof Spacing | number;
  pl?: keyof Spacing | number;
  m?: keyof Spacing | number;
  mx?: keyof Spacing | number;
  my?: keyof Spacing | number;
  mt?: keyof Spacing | number;
  mr?: keyof Spacing | number;
  mb?: keyof Spacing | number;
  ml?: keyof Spacing | number;
  radius?: number;
  backgroundColor?: string;
};

function resolveSize(
  value: keyof Spacing | number | undefined,
  getSpacing: (k: keyof Spacing) => number
): number | undefined {
  if (value === undefined) return undefined;
  if (typeof value === 'number') return value;
  return getSpacing(value);
}

export function Box({
  children,
  style,
  testID,
  p,
  px,
  py,
  pt,
  pr,
  pb,
  pl,
  m,
  mx,
  my,
  mt,
  mr,
  mb,
  ml,
  radius,
  backgroundColor,
}: BoxProps): React.ReactElement {
  const ui = uiSystemProvider();
  const s = ui.getSpacing.bind(ui);

  const computed: ViewStyle = {
    padding: resolveSize(p, s),
    paddingHorizontal: resolveSize(px, s),
    paddingVertical: resolveSize(py, s),
    paddingTop: resolveSize(pt, s),
    paddingRight: resolveSize(pr, s),
    paddingBottom: resolveSize(pb, s),
    paddingLeft: resolveSize(pl, s),
    margin: resolveSize(m, s),
    marginHorizontal: resolveSize(mx, s),
    marginVertical: resolveSize(my, s),
    marginTop: resolveSize(mt, s),
    marginRight: resolveSize(mr, s),
    marginBottom: resolveSize(mb, s),
    marginLeft: resolveSize(ml, s),
    borderRadius: radius,
    backgroundColor,
  } as ViewStyle;

  const normalized = Array.isArray(style)
    ? style.filter(Boolean)
    : style
      ? [style]
      : [];

  return (
    <View style={[computed, ...normalized]} testID={testID}>
      {children}
    </View>
  );
}
