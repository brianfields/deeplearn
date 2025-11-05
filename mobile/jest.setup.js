// Silence noisy console.log/error/warn during tests while preserving output on failure
const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;
const originalInfo = console.info;

beforeAll(() => {
  console.log = (...args) => {
    if (process.env.SHOW_TEST_LOGS === '1') {
      originalLog(...args);
    }
  };
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
  console.info = (...args) => {
    if (process.env.SHOW_TEST_LOGS === '1') {
      originalInfo(...args);
    }
  };
});

afterAll(() => {
  console.info = originalInfo;
  console.log = originalLog;
  console.error = originalError;
  console.warn = originalWarn;
});
