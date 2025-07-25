/**
 * TypeScript declarations for React Native type extensions
 *
 * This file extends React Native types to fix cross-platform compatibility issues
 */

import { TextStyle as RNTextStyle } from 'react-native';

declare module 'react-native' {
  interface TextStyle extends Omit<RNTextStyle, 'fontWeight'> {
    fontWeight?:
      | 'normal'
      | 'bold'
      | '100'
      | '200'
      | '300'
      | '400'
      | '500'
      | '600'
      | '700'
      | '800'
      | '900'
      | 100
      | 200
      | 300
      | 400
      | 500
      | 600
      | 700
      | 800
      | 900
      | 'ultralight'
      | 'thin'
      | 'light'
      | 'medium'
      | 'regular'
      | 'semibold'
      | 'condensedBold'
      | 'condensed'
      | 'heavy'
      | 'black'
      | string; // Allow any string for cross-platform compatibility
  }
}
