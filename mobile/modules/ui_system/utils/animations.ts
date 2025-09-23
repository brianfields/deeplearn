export const animationTimings = {
  micro: 160,
  ui: 220,
  modal: 320,
  stagger: 24,
} as const;

// CSS-like cubic-beziers represented as strings for documentation/usages where supported
export const animationEasing = {
  standard: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  exit: 'cubic-bezier(0.4, 0.0, 1, 1)',
} as const;

export function ms(duration: number): number {
  return duration;
}
