/**
 * UI System Unit Tests
 *
 * Tests theme management, component utilities, and design system functionality.
 */

import React from 'react';
import renderer, { act } from 'react-test-renderer';
import type { ReactTestInstance } from 'react-test-renderer';
import { UISystemService } from './service';
import { uiSystemProvider, ArtworkImage } from './public';
import { theme, colors, spacing, typography } from './theme/theme';

describe('UI System Module', () => {
  describe('UISystemService', () => {
    let service: UISystemService;

    beforeEach(() => {
      service = new UISystemService();
    });

    it('should initialize with default theme', () => {
      const currentTheme = service.getCurrentTheme();

      expect(currentTheme).toBeDefined();
      expect(currentTheme.colors).toBeDefined();
      expect(currentTheme.spacing).toBeDefined();
      expect(currentTheme.typography).toBeDefined();
    });

    it('should manage theme state', () => {
      const initialState = service.getThemeState();

      expect(initialState.isDarkMode).toBe(false);
      expect(initialState.systemTheme).toBe('auto');

      service.setDarkMode(true);
      const updatedState = service.getThemeState();
      expect(updatedState.isDarkMode).toBe(true);
    });

    it('should provide design system configuration', () => {
      const designSystem = service.getDesignSystem();

      expect(designSystem).toHaveProperty('theme');
      expect(designSystem).toHaveProperty('responsive');
      expect(designSystem).toHaveProperty('shadows');
      expect(designSystem).toHaveProperty('animations');
      expect(designSystem).toHaveProperty('utils');
    });

    it('should provide responsive utilities', () => {
      const responsive = service.getResponsiveConfig();

      expect(responsive).toHaveProperty('screenWidth');
      expect(responsive).toHaveProperty('screenHeight');
      expect(typeof service.isSmallScreen()).toBe('boolean');
      expect(typeof service.isMediumScreen()).toBe('boolean');
      expect(typeof service.isLargeScreen()).toBe('boolean');
    });

    it('should provide spacing utilities', () => {
      const mdSpacing = service.getSpacing('md');
      expect(typeof mdSpacing).toBe('number');
      expect(mdSpacing).toBe(16);
    });

    it('should provide color utilities', () => {
      const primaryColor = service.getColor('primary');
      expect(typeof primaryColor).toBe('string');
      expect(primaryColor).toBe('#0E3A53');

      const isLight = service.isLightColor('#FFFFFF');
      expect(isLight).toBe(true);

      const isDark = service.isLightColor('#000000');
      expect(isDark).toBe(false);
    });

    it('should provide typography utilities', () => {
      const heading1 = service.getTypography('heading1');

      expect(heading1).toHaveProperty('fontSize');
      expect(heading1).toHaveProperty('fontWeight');
      expect(heading1).toHaveProperty('lineHeight');
      expect(heading1.fontSize).toBe(28);
    });
  });

  describe('ArtworkImage component', () => {
    it('renders remote artwork when imageUrl is provided', () => {
      let tree: any;
      act(() => {
        tree = renderer.create(
          <ArtworkImage
            title="Galactic Algebra"
            imageUrl="https://cdn.example.com/galactic.png"
            description="Deco nebula geometry"
          />
        );
      });

      const imageNodes = tree.root.findAllByType('Image');
      expect(imageNodes).toHaveLength(1);
      expect(imageNodes[0].props.source).toEqual({
        uri: 'https://cdn.example.com/galactic.png',
      });
      expect(imageNodes[0].props.accessibilityLabel).toBe(
        'Deco nebula geometry'
      );
    });

    it('falls back to initials badge when no image is available', () => {
      let tree: any;
      act(() => {
        tree = renderer.create(<ArtworkImage title="Quantum Mechanics" />);
      });

      const imageNodes = tree.root.findAllByType('Image');
      expect(imageNodes).toHaveLength(0);

      const textNodes = tree.root.findAllByType('Text');
      expect(textNodes[0].props.children).toBe('QM');
    });

    it('shows fallback badge when the image fails to load', () => {
      let tree: any;
      act(() => {
        tree = renderer.create(
          <ArtworkImage
            title="Sonic Boom"
            imageUrl="https://cdn.example.com/sonic.png"
          />
        );
      });

      const imageNode = tree.root.findByType('Image');
      act(() => {
        imageNode.props.onError?.();
      });

      const updatedImageNodes = tree.root.findAllByType('Image');
      expect(updatedImageNodes).toHaveLength(0);

      const textNodes = tree.root.findAllByType('Text');
      expect(
        textNodes.some(
          (node: ReactTestInstance) => node.props.children === 'SB'
        )
      ).toBe(true);
    });
  });

  describe('Public Interface', () => {
    it('should provide ui system provider', () => {
      const provider = uiSystemProvider();

      expect(provider).toHaveProperty('getCurrentTheme');
      expect(provider).toHaveProperty('getThemeState');
      expect(provider).toHaveProperty('setDarkMode');
      expect(provider).toHaveProperty('setSystemTheme');
      expect(provider).toHaveProperty('getDesignSystem');
      expect(provider).toHaveProperty('isSmallScreen');
      expect(provider).toHaveProperty('isMediumScreen');
      expect(provider).toHaveProperty('isLargeScreen');
      expect(provider).toHaveProperty('getSpacing');
      expect(provider).toHaveProperty('getColor');
      expect(provider).toHaveProperty('isLightColor');
    });

    it('should return theme through provider', () => {
      const provider = uiSystemProvider();
      const currentTheme = provider.getCurrentTheme();

      expect(currentTheme).toBeDefined();
      expect(currentTheme.colors.primary).toBe('#0E3A53');
    });

    it('should manage dark mode through provider', () => {
      const provider = uiSystemProvider();

      const initialState = provider.getThemeState();
      expect(initialState.isDarkMode).toBe(false);

      provider.setDarkMode(true);
      const updatedState = provider.getThemeState();
      expect(updatedState.isDarkMode).toBe(true);
    });

    it('should provide responsive utilities through provider', () => {
      const provider = uiSystemProvider();

      expect(typeof provider.isSmallScreen()).toBe('boolean');
      expect(typeof provider.isMediumScreen()).toBe('boolean');
      expect(typeof provider.isLargeScreen()).toBe('boolean');
    });

    it('should provide spacing and color utilities through provider', () => {
      const provider = uiSystemProvider();

      const spacing = provider.getSpacing('lg');
      expect(spacing).toBe(24);

      const color = provider.getColor('secondary');
      expect(color).toBe('#C2A36B');

      const isLight = provider.isLightColor('#FFFFFF');
      expect(isLight).toBe(true);
    });
  });

  describe('Theme Constants', () => {
    it('should export theme constants', () => {
      expect(theme).toBeDefined();
      expect(colors).toBeDefined();
      expect(spacing).toBeDefined();
      expect(typography).toBeDefined();
    });

    it('should have correct color values', () => {
      expect(colors.primary).toBe('#0E3A53');
      expect(colors.secondary).toBe('#C2A36B');
      expect(colors.accent).toBe('#2F5D76');
    });

    it('should have correct spacing values', () => {
      expect(spacing.xs).toBe(4);
      expect(spacing.sm).toBe(8);
      expect(spacing.md).toBe(16);
      expect(spacing.lg).toBe(24);
      expect(spacing.xl).toBe(32);
      expect(spacing.xxl).toBe(48);
    });

    it('should have correct typography values', () => {
      expect(typography.heading1.fontSize).toBe(28);
      expect(typography.heading2.fontSize).toBe(22);
      expect(typography.body.fontSize).toBe(16);
      expect(typography.caption.fontSize).toBe(12);
    });
  });
});
