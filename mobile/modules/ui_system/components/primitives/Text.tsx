import React from 'react';
import {
  Text as RNText,
  TextProps as RNTextProps,
  TextStyle,
} from 'react-native';
import { uiSystemProvider } from '../../public';

export type TextVariant =
  | 'display'
  | 'h1'
  | 'h2'
  | 'title'
  | 'body'
  | 'secondary'
  | 'caption';

export interface TextProps extends RNTextProps {
  variant?: TextVariant;
  color?: string;
  weight?:
    | 'normal'
    | '600'
    | '700'
    | '800'
    | 'bold'
    | '100'
    | '200'
    | '300'
    | '400'
    | '500'
    | '900';
  align?: 'auto' | 'left' | 'right' | 'center' | 'justify';
}

export function Text({
  variant = 'body',
  color,
  weight,
  align,
  style,
  ...rest
}: TextProps): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();

  const base: TextStyle = (() => {
    switch (variant) {
      case 'display':
        return { fontSize: 32, lineHeight: 38, fontWeight: '800' } as TextStyle;
      case 'h1':
        return {
          fontSize: theme.typography.heading1.fontSize,
          lineHeight: theme.typography.heading1.lineHeight,
          fontWeight: theme.typography.heading1
            .fontWeight as TextStyle['fontWeight'],
        } as TextStyle;
      case 'h2':
        return {
          fontSize: theme.typography.heading2.fontSize,
          lineHeight: theme.typography.heading2.lineHeight,
          fontWeight: theme.typography.heading2
            .fontWeight as TextStyle['fontWeight'],
        } as TextStyle;
      case 'title':
        return { fontSize: 18, lineHeight: 24, fontWeight: '400' } as TextStyle;
      case 'secondary':
        return {
          fontSize: 14,
          lineHeight: 20,
          color: theme.colors.textSecondary,
        } as TextStyle;
      case 'caption':
        return {
          fontSize: 12,
          lineHeight: 16,
          color: theme.colors.textSecondary,
        } as TextStyle;
      case 'body':
      default:
        return {
          fontSize: theme.typography.body.fontSize,
          lineHeight: theme.typography.body.lineHeight,
          fontWeight: theme.typography.body
            .fontWeight as TextStyle['fontWeight'],
        } as TextStyle;
    }
  })();

  const computed: TextStyle = {
    color: color ?? theme.colors.text,
    textAlign: align,
    fontWeight: (weight as TextStyle['fontWeight']) ?? base.fontWeight,
    fontSize: base.fontSize,
    lineHeight: base.lineHeight,
  };

  const normalized = Array.isArray(style)
    ? style.filter(Boolean)
    : style
      ? [style]
      : [];

  return <RNText {...rest} style={[computed, ...normalized]} />;
}
