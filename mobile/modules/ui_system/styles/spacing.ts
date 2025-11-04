import { StyleSheet } from 'react-native';

/**
 * Shared spacing patterns for margins and padding
 * Eliminates repeated inline style definitions while maintaining design system consistency
 *
 * @example
 * import { spacingPatterns } from '../styles/spacing';
 * const spacing = spacingPatterns();
 * <View style={spacing.marginBottom12} />
 * <View style={[spacing.paddingHorizontal8, spacing.paddingVertical4]} />
 */

export function spacingPatterns(): ReturnType<typeof StyleSheet.create> {
  return StyleSheet.create({
    // ================================
    // Margins
    // ================================
    marginTop0: {
      marginTop: 0,
    },
    marginTop2: {
      marginTop: 2,
    },
    marginTop4: {
      marginTop: 4,
    },
    marginTop6: {
      marginTop: 6,
    },
    marginTop8: {
      marginTop: 8,
    },
    marginTop12: {
      marginTop: 12,
    },
    marginTop16: {
      marginTop: 16,
    },
    marginTop20: {
      marginTop: 20,
    },

    marginBottom0: {
      marginBottom: 0,
    },
    marginBottom2: {
      marginBottom: 2,
    },
    marginBottom4: {
      marginBottom: 4,
    },
    marginBottom6: {
      marginBottom: 6,
    },
    marginBottom8: {
      marginBottom: 8,
    },
    marginBottom12: {
      marginBottom: 12,
    },
    marginBottom16: {
      marginBottom: 16,
    },
    marginBottom20: {
      marginBottom: 20,
    },

    marginRight4: {
      marginRight: 4,
    },
    marginRight6: {
      marginRight: 6,
    },
    marginRight8: {
      marginRight: 8,
    },
    marginRight12: {
      marginRight: 12,
    },

    marginLeft4: {
      marginLeft: 4,
    },
    marginLeft8: {
      marginLeft: 8,
    },
    marginLeft12: {
      marginLeft: 12,
    },

    margin0: {
      margin: 0,
    },

    // ================================
    // Padding
    // ================================
    paddingVertical4: {
      paddingVertical: 4,
    },
    paddingVertical6: {
      paddingVertical: 6,
    },
    paddingVertical8: {
      paddingVertical: 8,
    },
    paddingVertical12: {
      paddingVertical: 12,
    },
    paddingVertical16: {
      paddingVertical: 16,
    },

    paddingHorizontal4: {
      paddingHorizontal: 4,
    },
    paddingHorizontal8: {
      paddingHorizontal: 8,
    },
    paddingHorizontal12: {
      paddingHorizontal: 12,
    },
    paddingHorizontal16: {
      paddingHorizontal: 16,
    },

    // Combined padding
    paddingVertical6Horizontal8: {
      paddingVertical: 6,
      paddingHorizontal: 8,
    },
    paddingVertical6Horizontal12: {
      paddingVertical: 6,
      paddingHorizontal: 12,
    },

    // ================================
    // Mixed margin/padding reset patterns
    // ================================
    marginBottomZeroPaddingZero: {
      marginBottom: 0,
      padding: 0,
    },
    marginZeroPaddingZero: {
      margin: 0,
      padding: 0,
    },

    marginRightZero: {
      marginRight: 0,
    },
  });
}
