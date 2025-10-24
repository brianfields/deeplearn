import '@testing-library/jest-dom/vitest';

// Polyfill navigator.clipboard for components that expect it in the browser.
if (typeof navigator !== 'undefined' && !navigator.clipboard) {
  // @ts-expect-error - defining minimal clipboard interface for tests
  navigator.clipboard = {
    writeText: async () => Promise.resolve(),
  };
}
