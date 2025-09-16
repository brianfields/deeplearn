# Mobile Learning App

React Native mobile app for the DeepLearn platform, built with Expo.

## Quick Start

```bash
# Install dependencies
npm install --legacy-peer-deps

# Start development server
npx expo start --ios
```

## E2E Testing

The app uses Maestro for end-to-end testing, which validates the complete user journey including backend integration.

### Setup

1. Install Java: https://www.oracle.com/java/technologies/downloads/
2. Maestro is already installed

### Running E2E Tests

```bash
# 1. Start backend server
cd ../backend && python3 server.py

# 2. Start mobile app
npx expo start --ios

# 3. Run E2E test
npm run e2e:maestro
```

See `MAESTRO_SETUP.md` for detailed setup instructions.

## Scripts

- `npm start` - Start Expo development server
- `npm run ios` - Start on iOS simulator
- `npm run android` - Start on Android emulator
- `npm test` - Run unit tests
- `npm run e2e:maestro` - Run E2E tests with Maestro
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Architecture

The app follows a modular architecture with feature-based modules:

- `modules/lesson_catalog/` - Lesson browsing and selection
- `modules/learning_session/` - Learning flow and progress tracking
- `modules/ui_system/` - Shared UI components and theme

## Testing

- **Unit Tests**: Jest for component and utility testing
- **E2E Tests**: Maestro for full user journey validation
- **Test IDs**: All interactive elements have `testID` attributes for testing
