# 🎯 Maestro E2E Testing

## Overview

Maestro provides end-to-end testing for the mobile learning app, validating the complete user journey from lesson selection through completion. It tests the full stack including React Native UI, API calls to the Python backend, and database operations.

## ✅ What's Ready

- **Maestro installed** - CLI is ready to use
- **Test file created** - `e2e/learning-flow.yaml` with complete user journey
- **Components instrumented** - All testID attributes already added
- **Backend ready** - Seed data created for testing

## ⚠️ Java Update Required

**Current Status:** You have Java 8, but Maestro requires Java 17+

### Quick Java 17 Installation

**Option 1: Download Java 17 (Recommended)**

1. Go to https://www.oracle.com/java/technologies/downloads/
2. Download **Java 17** for macOS
3. Install the `.dmg` file
4. Restart terminal
5. Verify: `java -version` should show 17+

**Option 2: Homebrew (if available)**

```bash
brew install openjdk@17
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Option 3: SDKMAN (Developer-friendly)

```bash
# Install SDKMAN
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"

# Install Java
sdk install java 11.0.19-tem
```

## 🚀 Running the E2E Test

Once Java is installed:

### 1. Start Backend Server

```bash
cd ../backend
python3 server.py
```

### 2. Start Mobile App

```bash
cd mobile
npx expo start --ios
# Wait for app to load in simulator
```

### 3. Run Maestro Test

```bash
# Add Maestro to PATH (if not done)
export PATH="$PATH":"$HOME/.maestro/bin"

# Run the E2E test
maestro test e2e/learning-flow.yaml
```

## 📋 What the Test Validates

The `learning-flow.yaml` test validates your complete user journey:

1. **App Launch** ✅ App opens and shows lesson catalog
2. **Lesson Selection** ✅ Taps first lesson card
3. **Session Start** ✅ Learning session creates and shows progress
4. **Didactic Content** ✅ Educational content displays and continues
5. **MCQ Questions** ✅ Multiple choice questions work (3 questions tested)
6. **Answer Feedback** ✅ Correct/incorrect feedback shows appropriately
7. **Results Screen** ✅ Score percentage displays correctly
8. **Return Navigation** ✅ "Continue Learning" returns to catalog

## 🔄 Full Stack Testing

This test validates your **entire application stack**:

- **Frontend**: React Native UI interactions
- **Navigation**: Screen transitions and state
- **API Calls**: HTTP requests to Python backend
- **Backend Logic**: Session creation, progress tracking
- **Database**: Lesson data, session storage
- **Real Data**: Uses your seed data (E2E Test Lesson)

## 🎯 Test Output

When successful, you'll see:

```
✅ Flow completed successfully
📱 All UI interactions worked
🔄 Backend integration validated
📊 Complete user journey tested
```

## 🐛 Troubleshooting

### Java Issues

```bash
# Verify Java installation
java --version

# Should show Java 11 or higher
```

### App Not Found

- Make sure Expo app is running in iOS Simulator
- Verify bundle identifier matches: `com.brian.deeplearn`

### Element Not Found

- Check that backend is running with seed data
- Verify testID attributes are correctly added
- Use Maestro Studio for debugging: `maestro studio`

## 📱 Package.json Scripts

Add these to your `package.json`:

```json
{
  "scripts": {
    "e2e:maestro": "maestro test e2e/learning-flow.yaml",
    "e2e:setup": "echo 'Start backend: python3 server.py' && echo 'Start app: npx expo start --ios'",
    "e2e:studio": "maestro studio"
  }
}
```

## 🎉 Next Steps

1. **Install Java** (see options above)
2. **Start backend server**
3. **Launch Expo app in simulator**
4. **Run `maestro test e2e/learning-flow.yaml`**
5. **Watch your complete user journey get validated!**

This gives you **true end-to-end testing** that validates your entire application stack, just like Playwright does for web apps! 🚀
