// Minimal NativeEventEmitter-compatible shim that does nothing.
class Subscription {
  remove() {}
}

class NativeEventEmitterShim {
  addListener() {
    return new Subscription();
  }
  removeAllListeners() {}
  removeSubscription() {}
  once() {
    return new Subscription();
  }
  emit() {
    return false;
  }
}

module.exports = NativeEventEmitterShim;
module.exports.default = NativeEventEmitterShim;
const noop = () => {};

class NativeEventEmitter {
  constructor() {}
  addListener() {
    return { remove: noop };
  }
  once() {
    return { remove: noop };
  }
  removeAllListeners() {}
  removeSubscription() {}
  emit() {}
}

module.exports = NativeEventEmitter;
module.exports.default = NativeEventEmitter;
