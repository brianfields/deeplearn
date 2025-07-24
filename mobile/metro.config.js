const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

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
config.resolver.sourceExts.push(
  'svg',
  'mjs',
  'cjs'
);

// Configure transformer for SVG and other assets
config.transformer.babelTransformerPath = require.resolve('react-native-svg-transformer');

// Exclude problematic modules for web
config.resolver.blockList = [
  /node_modules\/react-native-vector-icons\/.*\.flow$/,
];

module.exports = config;