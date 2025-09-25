// Reanimated motion presets (placeholder, no direct reanimated import to keep unit tests lean)
export const motionPresets = {
  fadeIn: { type: 'fadeIn', duration: 220 },
  fadeOut: { type: 'fadeOut', duration: 220 },
  slideUp: { type: 'slideUp', duration: 220 },
  slideDown: { type: 'slideDown', duration: 220 },
} as const;

/**
 * Reduced motion support
 * - Initializes from OS accessibility setting when available
 * - Safe for unit tests (guards against missing RN APIs in mocks)
 */
export type ReducedMotionController = {
  enabled: boolean;
  initialize(): void;
  setEnabled(forceEnabled: boolean): void;
};

export const reducedMotion: ReducedMotionController = {
  enabled: false,
  initialize(): void {
    try {
      // Lazy dynamic import to avoid hard dependency in tests and satisfy lint rules
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore - dynamic import without static type
      import('react-native')
        .then((RN: any) => {
          const AI = RN?.AccessibilityInfo;
          if (!AI) return;

          // Initial value
          if (typeof AI.isReduceMotionEnabled === 'function') {
            AI.isReduceMotionEnabled()
              .then((v: boolean) => {
                reducedMotion.enabled = !!v;
              })
              .catch(() => {
                /* noop */
              });
          }

          // Listen to changes (API differs across RN versions)
          const eventName = 'reduceMotionChanged';
          if (typeof AI.addEventListener === 'function') {
            const subscription = AI.addEventListener(
              eventName,
              (v: boolean) => {
                reducedMotion.enabled = !!v;
              }
            );
            void subscription;
          } else if (
            typeof AI?.setAccessibilityFocus === 'function' &&
            typeof RN?.DeviceEventEmitter?.addListener === 'function'
          ) {
            // Fallback to DeviceEventEmitter if present (rare)
            RN.DeviceEventEmitter.addListener(eventName, (v: boolean) => {
              reducedMotion.enabled = !!v;
            });
          }
        })
        .catch(() => {
          // Ignore dynamic import failures
        });
    } catch {
      // Ignore errors; keep default
    }
  },
  setEnabled(forceEnabled: boolean): void {
    reducedMotion.enabled = !!forceEnabled;
  },
};
