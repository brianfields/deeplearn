const { getDefaultConfig } = require('expo/metro-config');
const { resolve: metroResolve } = require('metro-resolver');
const path = require('path');

const config = getDefaultConfig(__dirname);

const aliasShim = relativePath =>
  path.resolve(__dirname, 'shims', relativePath);

// Enable symlinks and handle monorepo structure
config.resolver.nodeModulesPath = [
  path.resolve(__dirname, 'node_modules'),
  path.resolve(__dirname, '../node_modules'), // For shared packages
];

// Add support for additional asset types
config.resolver.assetExts.push(
  // Fonts
  'ttf',
  'otf',
  'woff',
  'woff2',
  // Images
  'webp',
  // Audio
  'mp3',
  'mp4',
  'wav',
  // Other
  'db',
  'json'
);

// Add support for additional source extensions
config.resolver.sourceExts.push('svg', 'mjs', 'cjs');

// Configure transformer for SVG and other assets
config.transformer.babelTransformerPath = require.resolve(
  'react-native-svg-transformer'
);

// Exclude problematic modules for web
config.resolver.blockList = [
  /node_modules\/react-native-vector-icons\/.*\.flow$/,
];

// Shim unsupported core RN native modules in Expo Go so the app can run.
// These aliases map to a no-op module under mobile/shims.
config.resolver.alias = {
  // Deprecated core modules that may be pulled by transitive deps
  PushNotificationIOS: aliasShim('pushNotificationIOSModule.js'),
  'react-native/Libraries/PushNotificationIOS/PushNotificationIOS': aliasShim(
    'pushNotificationIOSModule.js'
  ),
  'react-native/Libraries/PushNotificationIOS/RCTPushNotificationManager':
    aliasShim('nativePushNotificationManagerIOS.js'),
  'react-native/src/private/specs_DEPRECATED/modules/NativePushNotificationManagerIOS':
    aliasShim('nativePushNotificationManagerIOS.js'),
  'react-native/Libraries/EventEmitter/NativeEventEmitter': aliasShim(
    'nativeEventEmitter.js'
  ),
  Clipboard: aliasShim('emptyModule.js'),
  'react-native/Libraries/Components/Clipboard/Clipboard':
    aliasShim('emptyModule.js'),
  'react-native/Libraries/Components/ProgressBarAndroid/ProgressBarAndroid':
    aliasShim('emptyModule.js'),
};

// Intercept React Native's internal relative requires from react-native/index.js
// so references like './Libraries/PushNotificationIOS/PushNotificationIOS'
// resolve to our no-op shims when running in Expo Go.
config.resolver.resolveRequest = (context, moduleName, platform) => {
  try {
    const origin = context?.originModulePath || '';
    const isFromRNIndex = /node_modules[\/\\]react-native[\/\\]index\.js$/.test(
      origin
    );

    if (isFromRNIndex) {
      if (
        moduleName === './Libraries/PushNotificationIOS/PushNotificationIOS' ||
        moduleName === './Libraries/PushNotificationIOS/PushNotificationIOS.js'
      ) {
        return {
          filePath: aliasShim('pushNotificationIOSModule.js'),
          type: 'sourceFile',
        };
      }
      if (
        moduleName ===
          './Libraries/PushNotificationIOS/RCTPushNotificationManager' ||
        moduleName ===
          './src/private/specs_DEPRECATED/modules/NativePushNotificationManagerIOS'
      ) {
        return {
          filePath: aliasShim('nativePushNotificationManagerIOS.js'),
          type: 'sourceFile',
        };
      }
      if (
        moduleName === './Libraries/EventEmitter/NativeEventEmitter' ||
        moduleName === './Libraries/EventEmitter/NativeEventEmitter.js'
      ) {
        return {
          filePath: aliasShim('nativeEventEmitter.js'),
          type: 'sourceFile',
        };
      }
    }
  } catch {}

  // Always fall back to Metro's default resolver
  return metroResolve(context, moduleName, platform);
};

module.exports = config;
