module.exports = {
  testMatch: ['**/test_*_unit.(ts|tsx|js)'],
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/.expo/',
    '<rootDir>/dist/',
  ],
  collectCoverageFrom: [
    'modules/**/*.{ts,tsx}',
    'src/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/test_*_unit.{ts,tsx}',
    '!**/coverage/**',
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@modules/(.*)$': '<rootDir>/modules/$1',
    // Mock React Native modules
    '^react-native$': '<rootDir>/__mocks__/react-native.js',
    '^react-native-reanimated$':
      '<rootDir>/__mocks__/react-native-reanimated.js',
    '^@react-native-async-storage/async-storage$':
      '<rootDir>/__mocks__/async-storage.js',
    '^@react-native-community/netinfo$': '<rootDir>/__mocks__/netinfo.js',
    '^expo-haptics$': '<rootDir>/__mocks__/expo-haptics.js',
    '^expo-audio$': '<rootDir>/__mocks__/expo-audio.js',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testEnvironment: 'node',
  preset: 'ts-jest',
  transform: {
    '^.+\\.tsx?$': [
      'ts-jest',
      {
        useESM: true,
        tsconfig: {
          jsx: 'react',
        },
      },
    ],
  },
  globals: {
    __DEV__: true,
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
};
