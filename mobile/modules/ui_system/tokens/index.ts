// Weimar Edge Design Tokens
// Colors, spacing, radius, and typography scales

export const tokens = {
  radius: { sm: 4, md: 8, lg: 12, xl: 20, xxl: 28 },
  space: [0, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48] as const,
  color: {
    ink900: '#0D0E10',
    paper0: '#F2EFE6',
    accent600: '#0E3A53',
    accent400: '#2F5D76',
    accent200: '#C2D3DB',
    gilt500: '#C2A36B',
    rouge600: '#4A1F1F',
    emerald500: '#3C7A5A',
    amber600: '#D0822A',
    sky500: '#6BA3C8',
  },
  type: {
    display: { size: 32, line: 38, weight: '800', letter: -0.2 },
    h1: { size: 28, line: 34, weight: '700', letter: -0.3 },
    h2: { size: 22, line: 28, weight: '700', letter: -0.2 },
    title: { size: 18, line: 24, weight: '600', letter: -0.1 },
    body: { size: 16, line: 22, weight: '400', letter: 0 },
    secondary: { size: 14, line: 20, weight: '400', letter: 0, opacity: 0.8 },
    caption: { size: 12, line: 16, weight: '400', letter: 0, opacity: 0.7 },
  },
} as const;

export type Tokens = typeof tokens;
