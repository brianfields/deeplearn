import { StyleSheet } from 'react-native';

/**
 * Shared layout styles for common flexbox patterns
 * Use these instead of inline styles to maintain consistency and improve performance
 *
 * @example
 * import { layoutStyles } from '../styles/layout';
 * <View style={layoutStyles.row} />
 * <View style={[layoutStyles.flex1, { backgroundColor: theme.colors.surface }]} />
 */

export const layoutStyles = StyleSheet.create({
  // ================================
  // Flexbox Direction & Alignment
  // ================================
  row: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
  },

  rowStart: {
    flexDirection: 'row' as const,
    alignItems: 'flex-start' as const,
  },

  rowBetween: {
    flexDirection: 'row' as const,
    justifyContent: 'space-between' as const,
    alignItems: 'center' as const,
  },

  rowBetweenStart: {
    flexDirection: 'row' as const,
    justifyContent: 'space-between' as const,
    alignItems: 'flex-start' as const,
  },

  rowEnd: {
    flexDirection: 'row' as const,
    justifyContent: 'flex-end' as const,
    alignItems: 'center' as const,
  },

  column: {
    flexDirection: 'column' as const,
  },

  centered: {
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
  },

  centeredRow: {
    flexDirection: 'row' as const,
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
  },

  // ================================
  // Flex & Sizing
  // ================================
  flex1: {
    flex: 1,
  },

  flexShrink0: {
    flexShrink: 0,
  },

  flexShrink1: {
    flexShrink: 1,
  },

  // ================================
  // Reset/Cleanup
  // ================================
  noMargin: {
    margin: 0,
  },

  noPadding: {
    padding: 0,
  },

  noGap: {
    gap: 0,
  },

  // ================================
  // Typography
  // ================================
  fontWeightNormal: {
    fontWeight: '400' as const,
  },

  fontWeightMedium: {
    fontWeight: '500' as const,
  },

  fontWeightSemibold: {
    fontWeight: '600' as const,
  },

  fontWeightBold: {
    fontWeight: '700' as const,
  },

  // ================================
  // Self-Alignment (for individual items in flex containers)
  // ================================
  selfStart: {
    alignSelf: 'flex-start' as const,
  },

  selfCenter: {
    alignSelf: 'center' as const,
  },

  selfEnd: {
    alignSelf: 'flex-end' as const,
  },

  selfStretch: {
    alignSelf: 'stretch' as const,
  },

  // ================================
  // Overflow
  // ================================
  overflowHidden: {
    overflow: 'hidden' as const,
  },

  // ================================
  // Border Radius (common patterns)
  // ================================
  radiusSm: {
    borderRadius: 6,
  },

  radiusMd: {
    borderRadius: 12,
  },

  radiusLg: {
    borderRadius: 20,
  },

  radiusRound: {
    borderRadius: 999, // Fully rounded
  },

  radiusTopLarge: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },

  // ================================
  // Search overlay reset
  // ================================
  searchReset: {
    shadowOpacity: 0,
    elevation: 0,
  },

  // ================================
  // Margin utilities
  // ================================
  marginTop16: {
    marginTop: 16,
  },
});
