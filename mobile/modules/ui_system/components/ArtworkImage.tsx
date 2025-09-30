import React, { useMemo, useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

import { internalUiSystemProvider } from '../internalProvider';
import type { ArtworkImageProps } from '../models';

const uiSystemProvider = internalUiSystemProvider;

const VARIANT_PRESETS = {
  thumbnail: {
    width: 108,
    height: 108,
    borderRadius: 20,
  },
  hero: {
    width: '100%' as const,
    height: 220,
    borderRadius: 28,
  },
};

function computeInitials(title: string): string {
  if (!title) {
    return 'U';
  }

  const letters = title
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map(word => word[0]?.toUpperCase())
    .filter(Boolean);

  if (letters.length === 0) {
    const fallback = title
      .replace(/[^A-Za-z0-9]/g, '')
      .slice(0, 3)
      .toUpperCase();
    return fallback || 'U';
  }

  return letters.slice(0, 3).join('');
}

export const ArtworkImage: React.FC<ArtworkImageProps> = ({
  title,
  imageUrl,
  description,
  variant = 'thumbnail',
  style,
  testID,
}) => {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const designSystem = ui.getDesignSystem();
  const [loadError, setLoadError] = useState(false);

  const normalizedUrl = typeof imageUrl === 'string' ? imageUrl.trim() : '';
  const shouldShowImage = normalizedUrl.length > 0 && !loadError;

  const initials = useMemo(() => computeInitials(title), [title]);
  const preset = VARIANT_PRESETS[variant] ?? VARIANT_PRESETS.thumbnail;
  const shadowStyle =
    variant === 'hero'
      ? designSystem.shadows?.large
      : designSystem.shadows?.medium;

  return (
    <View
      testID={testID}
      style={[
        styles.base,
        { borderRadius: preset.borderRadius },
        variant === 'hero' ? styles.hero : styles.thumbnail,
        variant === 'hero'
          ? { width: preset.width, height: preset.height }
          : preset,
        shadowStyle,
        style,
      ]}
    >
      {shouldShowImage ? (
        <Image
          accessibilityLabel={description || `${title} artwork`}
          source={{ uri: normalizedUrl }}
          resizeMode="cover"
          onError={() => setLoadError(true)}
          style={[
            StyleSheet.absoluteFill,
            { borderRadius: preset.borderRadius },
          ]}
        />
      ) : (
        <View
          style={[
            styles.fallback,
            {
              borderRadius: preset.borderRadius,
              backgroundColor: theme.colors.primary,
              borderColor: theme.colors.accent,
            },
          ]}
          accessibilityLabel={`${title} initials badge`}
        >
          <Text style={[styles.initials, { color: theme.colors.surface }]}>
            {initials}
          </Text>
          {description ? (
            <Text
              numberOfLines={2}
              style={[
                styles.caption,
                {
                  color: ui.isLightColor(theme.colors.primary)
                    ? theme.colors.background
                    : theme.colors.surface,
                },
              ]}
            >
              {description}
            </Text>
          ) : null}
        </View>
      )}
      <View
        pointerEvents="none"
        style={[
          styles.frame,
          {
            borderRadius: preset.borderRadius,
            borderColor: ui.isLightColor(theme.colors.primary)
              ? theme.colors.accent
              : theme.colors.surface,
          },
        ]}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  base: {
    overflow: 'hidden',
    backgroundColor: '#0E3A53',
    position: 'relative',
  },
  thumbnail: {
    alignSelf: 'flex-start',
  },
  hero: {
    alignSelf: 'stretch',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  fallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
    paddingVertical: 16,
    borderWidth: 2,
  },
  initials: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: 2,
  },
  caption: {
    marginTop: 6,
    fontSize: 12,
    textAlign: 'center',
    opacity: 0.9,
  },
  frame: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderWidth: StyleSheet.hairlineWidth,
    borderStyle: 'solid',
  },
});

export default ArtworkImage;
