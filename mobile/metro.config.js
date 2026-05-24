// mobile folder में metro.config.js बनाओ/update करो:
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Node.js polyfills add करो
config.resolver.extraNodeModules = {
  crypto: require.resolve('crypto-browserify'),
  stream: require.resolve('stream-browserify'),
  vm: require.resolve('vm-browserify'),
};

config.resolver.sourceExts = [...config.resolver.sourceExts, 'cjs'];

module.exports = config;