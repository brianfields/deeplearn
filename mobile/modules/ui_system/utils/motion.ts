// Reanimated motion presets (placeholder, no direct reanimated import to keep unit tests lean)
export const motionPresets = {
  fadeIn: { type: 'fadeIn', duration: 220 },
  fadeOut: { type: 'fadeOut', duration: 220 },
  slideUp: { type: 'slideUp', duration: 220 },
  slideDown: { type: 'slideDown', duration: 220 },
} as const;

export const reducedMotion = {
  enabled: false,
};
