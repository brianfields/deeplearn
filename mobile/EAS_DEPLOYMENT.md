# Mobile App Deployment with EAS (Expo Application Services)

## Overview

The mobile app is built with React Native and Expo, and should be deployed using **Expo Application Services (EAS)**, not Echo.

## Quick Reference: Build Types and Access Control

| Build Type                     | Purpose                        | Distribution           | Who Can Access                           | How to Track Users                    | Account Required                  |
| ------------------------------ | ------------------------------ | ---------------------- | ---------------------------------------- | ------------------------------------- | --------------------------------- |
| **Development**                | Active development & debugging | Local (USB/simulator)  | Developers only                          | N/A (local only)                      | Expo only                         |
| **Preview (iOS)**              | Beta testing                   | TestFlight             | Internal testers (100) or External (10k) | App Store Connect dashboard           | Expo + Apple Developer ($99/yr)   |
| **Preview (Android - Play)**   | Beta testing                   | Play Console tracks    | Email list (unlimited)                   | Play Console dashboard                | Expo + Google Play ($25 one-time) |
| **Preview (Android - Direct)** | Quick testing                  | Direct APK download    | Anyone with link                         | Download count only (no user details) | Expo only                         |
| **Production**                 | Public release                 | App Store / Play Store | Public                                   | Store analytics                       | Expo + Apple/Google accounts      |

### Key Takeaways

1. **Development builds**: For developers only, installed locally
2. **Preview builds**: For testers, with controlled access via TestFlight/Play Console
3. **Production builds**: For everyone, distributed via app stores
4. **User tracking**: Best with TestFlight/Play Console; limited with direct APK distribution
5. **Account costs**:
   - Expo: Free for basic use
   - Apple: $99/year for iOS distribution
   - Google: $25 one-time for Android distribution

## Prerequisites

### Required Accounts

1. **Expo Account** (all build types):
   - Sign up at [expo.dev](https://expo.dev)
   - Free tier supports basic builds
   - Paid tier required for teams and priority builds

2. **Apple Developer Account** (iOS only):
   - Required for: TestFlight and App Store distribution
   - Cost: $99/year
   - Sign up at [developer.apple.com](https://developer.apple.com)
   - Not needed for development builds

3. **Google Play Developer Account** (Android only):
   - Required for: Play Store distribution (including internal testing)
   - Cost: $25 one-time fee
   - Sign up at [play.google.com/console](https://play.google.com/console)
   - Not needed for development builds or direct APK distribution

### CLI Setup

1. Install EAS CLI:

   ```bash
   npm install -g eas-cli
   ```

2. Login to Expo:

   ```bash
   eas login
   ```

3. Configure your project:
   ```bash
   cd mobile
   eas build:configure
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

## Complete Workflow

### First-Time Setup

1. **Create accounts** (if you haven't already):
   - Expo account
   - Apple Developer account (for iOS)
   - Google Play Developer account (for Android)

2. **Register your app**:
   - iOS: Create app identifier in Apple Developer portal
   - Android: Create app in Google Play Console

3. **Configure EAS**:
   ```bash
   cd mobile
   eas build:configure
   ```

### Development Workflow

1. **Build for development**:

   ```bash
   eas build --profile development --platform ios
   # or
   eas build --profile development --platform android
   ```

2. **Install on your device**:
   ```bash
   eas build:run --profile development --platform ios
   ```

### Preview/Testing Workflow

1. **Build preview version**:

   ```bash
   eas build --profile preview --platform ios
   eas build --profile preview --platform android
   ```

2. **Submit to testing platforms**:

   **iOS (TestFlight)**:

   ```bash
   eas submit --platform ios
   ```

   - Then add testers in App Store Connect
   - Testers receive email invitation
   - They install via TestFlight app

   **Android (Play Console)**:

   ```bash
   eas submit --platform android --track internal
   ```

   - Add tester emails in Play Console
   - Share opt-in link with testers
   - They opt-in and install from Play Store

   **Android (Direct APK)**:
   - Build creates shareable link in EAS dashboard
   - Share link with testers
   - They download and install APK

3. **Monitor testing**:
   - Check tester activity in App Store Connect/Play Console
   - Review crash reports and feedback
   - Iterate based on feedback

### Production Workflow

1. **Build for production**:

   ```bash
   eas build --profile production --platform ios
   eas build --profile production --platform android
   ```

2. **Submit to app stores**:

   ```bash
   eas submit --platform ios
   eas submit --platform android
   ```

3. **App Store review**:
   - iOS: Typically 1-3 days
   - Android: Typically a few hours to a day

4. **Release**:
   - Manually release or enable automatic release
   - Monitor for crashes and user feedback

## Build Types Explained

### Development Builds

- **Purpose**: For active development and debugging
- **Audience**: Developers only
- **Distribution**: Local installation only (via USB, simulator, or Expo Go)
- **Access**: Anyone with the build file can install it
- **Features**: Includes development tools, hot reload, debugger access
- **Use case**: Testing new features during development

### Preview Builds

- **Purpose**: Internal testing and QA
- **Audience**: Internal testers, QA team, stakeholders
- **Distribution**:
  - iOS: TestFlight (requires Apple Developer account)
  - Android: Internal testing track or direct APK download
- **Access**: Controlled via TestFlight/Play Console or EAS dashboard
- **Features**: Production-like build but with internal distribution
- **Use case**: Beta testing, stakeholder reviews, pre-release validation

### Production Builds

- **Purpose**: Public release
- **Audience**: All app store users
- **Distribution**: App Store (iOS) and Google Play Store (Android)
- **Access**: Public (anyone can download from stores)
- **Features**: Fully optimized, production configuration
- **Use case**: Official releases to end users

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

## Managing Testers and Access

### iOS Preview/TestFlight Distribution

#### Adding Testers

1. **Via App Store Connect** (recommended for iOS):
   - Go to [App Store Connect](https://appstoreconnect.apple.com)
   - Navigate to your app → TestFlight
   - Click "+" to add internal or external testers
   - Internal testers: Up to 100 users with App Store Connect access
   - External testers: Up to 10,000 users (requires Beta App Review)

2. **Via EAS CLI**:

   ```bash
   # Submit to TestFlight
   eas submit --platform ios

   # Then add testers in App Store Connect
   ```

#### Viewing TestFlight Testers

- App Store Connect → TestFlight → Testers
- See who has installed, session data, and crash reports
- Export tester list as CSV

#### Complete TestFlight Invitation Flow

**For New/Unregistered Testers**:

1. **Developer submits build**:

   ```bash
   eas build --profile preview --platform ios
   eas submit --platform ios --profile preview
   ```

2. **Developer adds tester in App Store Connect**:
   - TestFlight → Internal/External Testing → Add Tester
   - Enter tester's email address

3. **Tester receives email**:
   - Subject: "You're invited to test [App Name]"
   - Contains TestFlight download link (if needed)
   - Contains app-specific invitation/redeem code

4. **Tester installs TestFlight** (if not already installed):
   - Click TestFlight link in email → App Store → Install
   - Or manually search "TestFlight" in App Store

5. **Tester accepts invitation**:
   - Option A: Click "View in TestFlight" link in email
   - Option B: Open TestFlight app → Redeem → Enter code from email

6. **Tester installs your app**:
   - TestFlight opens showing your app
   - Tap "Install" or "Accept"
   - App downloads and installs

7. **Testing**:
   - Tester can provide feedback via TestFlight
   - Crashes automatically reported to you
   - You can see tester activity in App Store Connect

**Important Notes**:

- Tester's email must match their Apple ID email
- External testers: First build requires Beta App Review (1-2 days wait)
- Internal testers: Immediate access, but limited to 100 users
- Invitations expire after 90 days if not accepted
- Builds expire after 90 days (testers need to update)

### Android Preview Distribution

#### Option 1: Internal Testing Track (Google Play Console)

1. **Setup**:
   - Go to [Google Play Console](https://play.google.com/console)
   - Select your app → Testing → Internal testing
   - Create an email list of testers

2. **Add Testers**:

   ```bash
   # Submit to internal testing track
   eas submit --platform android --track internal
   ```

   - Then add testers in Play Console → Internal testing → Testers
   - Share the opt-in URL with testers

3. **View Access**:
   - Play Console → Internal testing → Shows testers and installation status

#### Option 2: Direct APK Distribution (EAS Dashboard)

1. **Build and Share**:

   ```bash
   eas build --profile preview --platform android
   ```

2. **Manage Access via EAS**:
   - Visit [expo.dev](https://expo.dev) → Your project → Builds
   - Each build has a shareable link
   - You can see who has downloaded builds in the EAS dashboard

3. **View Downloads**:
   - EAS Dashboard shows download counts and access logs
   - Note: Cannot track individual users with direct APK distribution

### Development Build Distribution

For development builds, you typically:

1. Install directly via USB or simulator
2. Share via EAS links (less common for dev builds)
3. No formal tester registration needed

## Submission

### iOS App Store

```bash
eas submit --platform ios
```

### Android Play Store

```bash
# Production submission
eas submit --platform android

# Internal testing track
eas submit --platform android --track internal

# Closed testing track
eas submit --platform android --track closed

# Open testing track (beta)
eas submit --platform android --track open
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

## Viewing Build Status and User Analytics

### EAS Dashboard

Visit [expo.dev](https://expo.dev) to access your project dashboard:

1. **Build Status**:
   - View all builds (in-progress, completed, failed)
   - Download build artifacts
   - See build logs and error messages
   - Share build links with testers

2. **Build Analytics**:
   - Track build success/failure rates
   - Monitor build times
   - View download counts for shared builds

### TestFlight Analytics (iOS)

In App Store Connect → TestFlight:

- **Tester Activity**: Who installed, when, which version
- **Session Data**: Usage statistics per tester
- **Crash Reports**: Crashes and stack traces
- **Feedback**: In-app feedback from testers
- **Export Data**: Download tester lists and metrics

### Google Play Console Analytics (Android)

In Play Console → Testing:

- **Internal/Closed/Open Testing Stats**: Installation numbers
- **Tester Lists**: Who has access, who has installed
- **Crash Reports**: ANR and crash analytics
- **Pre-launch Reports**: Automated testing results
- **Feedback**: Reviews from testers

### Checking Who Can Access What

#### iOS (TestFlight)

```bash
# List all builds
eas build:list --platform ios

# Then check App Store Connect for testers per build
```

- App Store Connect → TestFlight → Testers tab shows all users
- Each build group shows which testers have access
- Individual tester view shows which builds they've installed

#### Android (Play Console)

```bash
# List all builds
eas build:list --platform android

# For Play Store testing tracks:
```

- Play Console → Testing → Select track (Internal/Closed/Open)
- Testers tab shows email list and opt-in status
- Statistics tab shows install counts

#### Android (Direct APK via EAS)

```bash
# View build history
eas build:list --platform android --buildProfile preview
```

- EAS dashboard shows download counts (not individual users)
- Cannot track specific users with direct APK distribution
- Consider using Play Console internal testing for better tracking

## Useful CLI Commands

### Build Management

```bash
# List all builds
eas build:list

# List builds for specific platform
eas build:list --platform ios
eas build:list --platform android

# List builds for specific profile
eas build:list --platform ios --buildProfile preview

# View build details
eas build:view [BUILD_ID]

# Cancel a running build
eas build:cancel [BUILD_ID]

# Download build artifacts
eas build:download [BUILD_ID]

# Run/install a build
eas build:run --platform ios --id [BUILD_ID]
```

### Submission Management

```bash
# View submission history
eas submit:list

# View specific submission
eas submit:view [SUBMISSION_ID]
```

### Project Info

```bash
# View project configuration
eas config

# View credentials
eas credentials

# View project metadata
eas metadata:pull
eas metadata:push
```

### Update Management (OTA Updates)

```bash
# Publish an update
eas update --branch preview --message "Bug fixes"

# View updates
eas update:list

# View update details
eas update:view [UPDATE_ID]

# Configure channels
eas channel:create [CHANNEL_NAME]
eas channel:list
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
6. **Build Quotas**: Free Expo accounts have limited build minutes; upgrade for production use
7. **Certificates**: EAS manages certificates automatically; manual management is rarely needed
8. **Version Bumping**: Remember to increment version numbers in `app.json` for each release

## Common Scenarios and FAQs

### How do I add a single tester?

**iOS (TestFlight) - Step by Step**:

1. **Ensure you have a build submitted**:

   ```bash
   # Build and submit to TestFlight first
   eas build --profile preview --platform ios
   eas submit --platform ios --profile preview
   ```

   Wait 10-30 minutes for processing

2. **Add the tester in App Store Connect**:
   - Go to [App Store Connect](https://appstoreconnect.apple.com)
   - Click **My Apps** → Select your app
   - Click **TestFlight** tab
   - Choose tester type:
     - **Internal Testers** (for team members): Click "Internal Testing" → "+" → Add Users
     - **External Testers** (for anyone else): Click "External Testing" → Create a group if needed → "+" → Add Testers

3. **Enter tester information**:
   - Enter their email address
   - (Optional) Add first and last name
   - Click **Add**

4. **What the tester receives**:
   - Email invitation from TestFlight
   - Subject: "You're invited to test [Your App Name]"
   - Contains instructions and TestFlight link

5. **What the tester needs to do**:
   - Download TestFlight app from App Store (if not installed)
   - Open the invitation email on their iOS device
   - Click "View in TestFlight" or "Accept"
   - TestFlight app opens and shows your app
   - Tap "Install" to download your app

6. **Tester doesn't have TestFlight?**:
   - The invitation email includes a link to download TestFlight
   - Once installed, they can click the invitation link again
   - Or they can search for your app in TestFlight using the redeem code from the email

**Note**: External testers require Beta App Review for the first build (1-2 days). Internal testers get instant access.

**Android (Play Console)**:

1. Go to Play Console → Testing → Internal testing
2. Add their email to the tester list
3. Share the opt-in URL
4. They opt-in and install from Play Store

**Android (Direct)**:

1. Build with `eas build --profile preview --platform android`
2. Get shareable link from EAS dashboard
3. Send link to tester
4. They download and install APK

### How do I see who has installed my preview build?

**iOS**: App Store Connect → TestFlight → Select your app → Testers tab shows installation status

**Android (Play Console)**: Play Console → Testing → Select track → View statistics

**Android (Direct APK)**: EAS dashboard shows total downloads but not individual users

### What's the difference between internal and external testers on TestFlight?

**Internal Testers**:

- Up to 100 users
- Must have App Store Connect access (team members)
- No App Review required
- Instant access to new builds

**External Testers**:

- Up to 10,000 users
- Don't need App Store Connect access
- First build requires Beta App Review (1-2 days)
- Subsequent builds auto-approved if similar

### How long do builds take?

- **Development**: 10-20 minutes
- **Preview**: 15-25 minutes
- **Production**: 15-30 minutes

Times vary based on:

- Platform (iOS usually slower than Android)
- EAS build queue (free accounts may wait)
- Dependencies and native modules

### Can I test a build before sending to testers?

Yes! Use `eas build:run` to install directly on your device/simulator:

```bash
eas build:run --profile preview --platform ios
```

### How do I revoke access for a tester?

**iOS**: App Store Connect → TestFlight → Testers → Select tester → Remove

**Android (Play Console)**: Remove from tester email list

**Android (Direct APK)**: Cannot revoke; build new version if needed

### What happens when I delete a build from EAS?

- Build artifacts are removed from EAS servers
- Shareable links stop working
- Already installed apps continue to work
- TestFlight/Play Store builds are unaffected (managed separately)

## Troubleshooting Common Issues

### Build Failures

**Issue**: Build fails with "No matching distribution found for [package]"

- **Solution**: Check `package.json` and ensure all dependencies are compatible with React Native/Expo

**Issue**: Build fails with certificate/provisioning errors (iOS)

- **Solution**: Run `eas credentials` and regenerate certificates, or let EAS manage them automatically

**Issue**: Build stuck in queue

- **Solution**: Free tier has limited workers; upgrade account or wait for queue to clear

### Submission Failures

**Issue**: iOS submission rejected - "Missing compliance"

- **Solution**: Answer export compliance questions in App Store Connect before submitting

**Issue**: Android submission fails - "Version code already exists"

- **Solution**: Increment version code in `app.json` before building

**Issue**: TestFlight build not appearing

- **Solution**: Check email for processing notification; can take 10-30 minutes

### Tester Access Issues

**Issue**: Tester not receiving TestFlight invitation

- **Solution**:
  1. Check spam folder
  2. Verify email address is correct in App Store Connect
  3. Resend invitation from TestFlight → Testers → Select tester → Resend Invite
  4. Try adding with a different email address
  5. Make sure the build has finished processing (can take 10-30 minutes)

**Issue**: Tester clicks invitation but nothing happens

- **Solution**:
  1. Ensure TestFlight app is installed (download from App Store)
  2. Try copying the invitation link and pasting in Safari
  3. Use the redeem code from email: Open TestFlight → Redeem → Enter code
  4. Check they're signed in to the App Store with the correct Apple ID

**Issue**: "This beta is full" message in TestFlight

- **Solution**:
  1. External tester groups have max capacity limits
  2. Create a new group in App Store Connect
  3. Or remove inactive testers to make room

**Issue**: "This beta isn't accepting any new testers" message

- **Solution**:
  1. External testing may be paused in App Store Connect
  2. Go to TestFlight → External Testing → Resume testing
  3. For first build, wait for Beta App Review approval

**Issue**: Tester sees "No apps available to test"

- **Solution**:
  1. They may be signed in with wrong Apple ID
  2. Verify the email address matches their Apple ID
  3. Invitation may have expired (resend from App Store Connect)

**Issue**: Android tester can't access internal testing

- **Solution**:
  1. Ensure they're on the email list
  2. Share the correct opt-in URL
  3. Verify they're signed in to Play Store with correct Google account

**Issue**: Direct APK won't install on Android

- **Solution**:
  1. Enable "Install from Unknown Sources" in Android settings
  2. Ensure device meets minimum Android version
  3. Uninstall previous version if signature mismatch

### Environment Variable Issues

**Issue**: App can't reach backend API

- **Solution**:
  1. Verify `EXPO_PUBLIC_API_BASE_URL` is set correctly in `eas.json`
  2. Check backend CORS configuration
  3. Ensure backend is deployed and accessible

**Issue**: Environment variables not available in app

- **Solution**:
  1. Ensure variable has `EXPO_PUBLIC_` prefix
  2. Rebuild the app (env vars are baked in at build time)
  3. Check `eas.json` build profile configuration

### Getting Help

1. **Check build logs**: `eas build:view [BUILD_ID]` shows detailed logs
2. **EAS Dashboard**: [expo.dev](https://expo.dev) has visual logs and error messages
3. **Expo Forums**: [forums.expo.dev](https://forums.expo.dev)
4. **Discord**: Join Expo Discord for community support
5. **Documentation**: [docs.expo.dev](https://docs.expo.dev)

## Resources

### Official Documentation

- [EAS Build Documentation](https://docs.expo.dev/build/introduction/)
- [EAS Submit Documentation](https://docs.expo.dev/submit/introduction/)
- [EAS Update Documentation](https://docs.expo.dev/eas-update/introduction/)
- [App Store Connect Help](https://developer.apple.com/app-store-connect/)
- [Google Play Console Help](https://support.google.com/googleplay/android-developer)

### Platform-Specific Guides

- [TestFlight Beta Testing Guide](https://developer.apple.com/testflight/)
- [Google Play Internal Testing](https://support.google.com/googleplay/android-developer/answer/9845334)
- [Managing iOS Certificates](https://docs.expo.dev/app-signing/app-credentials/)
- [Android App Signing](https://docs.expo.dev/app-signing/app-credentials/)

### Community Resources

- [Expo Forums](https://forums.expo.dev)
- [Expo Discord](https://chat.expo.dev)
- [Expo GitHub](https://github.com/expo/expo)

### Quick Links

- [EAS Dashboard](https://expo.dev)
- [App Store Connect](https://appstoreconnect.apple.com)
- [Google Play Console](https://play.google.com/console)
