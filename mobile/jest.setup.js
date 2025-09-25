// Silence noisy console.error/warn during tests while preserving output on failure
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (process.env.SHOW_TEST_LOGS === '1') {
      originalError(...args);
    }
  };
  console.warn = (...args) => {
    if (process.env.SHOW_TEST_LOGS === '1') {
      originalWarn(...args);
    }
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});
