/**
 * Card Component for React Native Learning App
 *
 * A flexible card container with consistent styling
 */

import React from 'react'
import { View, StyleSheet, ViewStyle } from 'react-native'
import { colors, spacing, shadows } from '@/utils/theme'

interface CardProps {
  children: React.ReactNode
  style?: ViewStyle
  elevated?: boolean
  padding?: keyof typeof spacing | number
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  elevated = true,
  padding = 'md'
}) => {
  const paddingValue = typeof padding === 'number' ? padding : spacing[padding]

  const cardStyle = [
    styles.base,
    elevated && shadows.medium,
    { padding: paddingValue },
    style
  ]

  return (
    <View style={cardStyle}>
      {children}
    </View>
  )
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
  }
})

export default Card