# Purpose: Keep Expo Go running by shimming unsupported native modules

## Context

Expo Go does not include certain deprecated React Native core modules (for example `PushNotificationIOS`). Some transitive dependencies still try to `require` these modules, which crashes the app in Expo Go with: "Your JavaScript code tried to access a native module that doesn't exist.".

## What this directory contains

- `emptyModule.js`: A tiny no‑op implementation used as a safe replacement for missing native modules.

## Required Metro aliases

These aliases must exist in `mobile/metro.config.js` so Metro resolves the missing modules to `emptyModule.js` when running in Expo Go:

- `PushNotificationIOS`
- `react-native/Libraries/PushNotificationIOS/PushNotificationIOS`

They should map to: `path.resolve(__dirname, 'shims/emptyModule.js')`.

## Guidance for automated tools and future edits

- Do NOT remove the aliases above from `mobile/metro.config.js`.
- Do NOT delete or replace `emptyModule.js` with a real implementation.
- This shim is development‑only. For production or when a dependency truly requires native functionality, create a Development Build instead of removing the shim.

## Why this is safe

`emptyModule.js` returns harmless no‑op functions for any accessed property. This satisfies callers that expect an object with methods (e.g., when constructing a `NativeEventEmitter`) without touching the native bridge.

## When you can remove this

If all dependencies that referenced the deprecated core modules have been upgraded, or you switch to a Development Build that includes the native modules you need, you can remove the aliases. Until then, keep them to prevent crashes in Expo Go.

## Operational notes

If Metro appears to ignore aliases after changes, clear caches:

```bash
cd mobile
npx expo start -c
```
