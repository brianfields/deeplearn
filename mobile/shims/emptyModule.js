// No-op shim for unsupported native modules in Expo Go.
// Exposes functions that do nothing to prevent runtime crashes.
module.exports = new Proxy(function () {}, {
  get: () => () => {},
  apply: () => {},
});
