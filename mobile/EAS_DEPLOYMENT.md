# Mobile App Deployment with EAS (Expo Application Services)

## Overview

The mobile app is built with React Native and Expo, and should be deployed using **Expo Application Services (EAS)**, not Echo.

## Prerequisites

1. Install EAS CLI:

   ```bash
   npm install -g eas-cli
   ```

2. Login to Expo:
   ```bash
   eas login
   ```

## Configuration

### 1. Create `eas.json` in the mobile directory:

```json
{
  "cli": {
    "version": ">= 13.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "env": {
        "EXPO_PUBLIC_API_BASE_URL": "http://localhost:8000"
      }
    },
    "preview": {
      "distribution": "internal",
      "env": {
        "EXPO_PUBLIC_API_BASE_URL": "https://lantern-room-backend.onrender.com"
      }
    },
    "production": {
      "env": {
        "EXPO_PUBLIC_API_BASE_URL": "https://lantern-room-backend.onrender.com"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

### 2. Update `mobile/modules/infrastructure/public.ts`

Update the production API URL:

```typescript
const DEFAULT_HTTP_CONFIG: HttpClientConfig = {
  baseURL: __DEV__
    ? DEV_BASE_URL
    : process.env.EXPO_PUBLIC_API_BASE_URL ||
      'https://lantern-room-backend.onrender.com',
  timeout: 30000,
  retryAttempts: 3,
};
```

**Note:** The environment variable must be prefixed with `EXPO_PUBLIC_` to be accessible in the app (similar to Next.js's `NEXT_PUBLIC_` prefix).

## Build Commands

### iOS

```bash
# Development build (for testing on simulator/device)
eas build --profile development --platform ios

# Preview build (internal distribution via TestFlight)
eas build --profile preview --platform ios

# Production build (App Store)
eas build --profile production --platform ios
```

### Android

```bash
# Development build (for testing)
eas build --profile development --platform android

# Preview build (internal distribution)
eas build --profile preview --platform android

# Production build (Google Play)
eas build --profile production --platform android
```

## Submission

### iOS App Store

```bash
eas submit --platform ios
```

### Android Play Store

```bash
eas submit --platform android
```

## Environment Variables

The mobile app needs to know the backend API URL:

- **Development**: Uses localhost/emulator addresses (already configured)
- **Preview/Production**: Uses your Render backend URL

Set this in `eas.json` (see above) or pass via build command:

```bash
eas build --profile production --platform ios --non-interactive \
  --build-env EXPO_PUBLIC_API_BASE_URL=https://lantern-room-backend.onrender.com
```

## Testing Preview Builds

After building a preview:

1. iOS: Use TestFlight or install via EAS CLI

   ```bash
   eas build:run --profile preview --platform ios
   ```

2. Android: Download APK from EAS dashboard or install via CLI
   ```bash
   eas build:run --profile preview --platform android
   ```

## Continuous Deployment

You can integrate EAS with GitHub Actions for automatic builds:

1. Generate an EAS access token:

   ```bash
   eas build:configure
   ```

2. Add the token to GitHub Secrets as `EXPO_TOKEN`

3. Create `.github/workflows/eas-build.yml`:
   ```yaml
   name: EAS Build
   on:
     push:
       branches: [main]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-node@v3
           with:
             node-version: 18
         - run: npm install -g eas-cli
         - run: eas build --platform all --non-interactive --profile preview
           env:
             EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
   ```

## Important Notes

1. **Backend URL**: Make sure the mobile app's API base URL matches your Render backend service URL
2. **CORS**: Ensure your backend CORS settings allow requests from the mobile app
3. **Authentication**: If using OAuth, update redirect URLs in your identity provider
4. **Push Notifications**: If implementing push notifications, you'll need to configure EAS Push
5. **Updates**: Use EAS Update for OTA (over-the-air) updates without app store submission

## Resources

- [EAS Build Documentation](https://docs.expo.dev/build/introduction/)
- [EAS Submit Documentation](https://docs.expo.dev/submit/introduction/)
- [EAS Update Documentation](https://docs.expo.dev/eas-update/introduction/)
