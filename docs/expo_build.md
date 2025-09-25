Expo builds, native modules, and running in Expo Go
===================================================

Context
-------
While running the mobile app in Expo Go on iOS, we saw:

- “Your JavaScript code tried to access a native module that doesn't exist.”
- Call stack implicated `PushNotificationIOS` (deprecated in RN core and not included in Expo Go).
- Additional warnings about `Clipboard` and `ProgressBarAndroid` being extracted from RN core.

Root cause
----------
Transitive dependencies can still require old core modules (e.g., `PushNotificationIOS`), which are not present in Expo Go. This causes a hard crash even if our app doesn’t directly use them.

Short‑term workaround (keeps Expo Go workflow)
----------------------------------------------
We added Metro resolver aliases to map these modules to a no‑op shim so Expo Go won’t crash:

- File: `mobile/metro.config.js` → `config.resolver.alias`
- Shim: `mobile/shims/emptyModule.js`

Aliased modules:

- `PushNotificationIOS`
- `react-native/Libraries/PushNotificationIOS/PushNotificationIOS`
- `Clipboard`
- `react-native/Libraries/Components/Clipboard/Clipboard`
- `react-native/Libraries/Components/ProgressBarAndroid/ProgressBarAndroid`

Tradeoffs of shimming:

- Those features are disabled in Expo Go (no-ops). App won’t crash, but push notifications, clipboard, or Android progress bar behaviors won’t function in Expo Go.
- This is development-only. Production or a dev build should implement real functionality.

Long‑term solution (Development Build)
--------------------------------------
Create a development build that includes native modules you need:

- Local: `npx expo run:ios`
- Cloud: `eas build -p ios --profile development`

Benefits:

- Full native module support, still with Metro, fast refresh, and debugging.
- Required when a dependency uses modules not bundled in Expo Go.

Notes on our codebase
---------------------
- We harden `NetInfo` usage to avoid crashes if it’s unavailable in Expo Go (assume online in dev): see `mobile/modules/infrastructure/repo.ts`.
- We added Reanimated plugin and early imports for RN Gesture Handler/Reanimated: `mobile/babel.config.js`, `mobile/index.ts`.
- We removed a require cycle in `ui_system` by introducing `internalProvider.ts` and updating internal components to use it.

Operational tips
----------------
- Clear caches when Metro behaves oddly: `npx expo start -c`, remove `~/.expo/cache`, clear Simulator content.
- Keep Expo and plugins within the expected patch versions for best compatibility.
