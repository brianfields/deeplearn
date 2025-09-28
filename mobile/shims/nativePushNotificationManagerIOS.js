// No-op shim for internal NativePushNotificationManagerIOS spec used by RN.
module.exports = new Proxy(
  {},
  {
    get: () => () => {},
  }
);
const noop = () => {};
const noopPromise = async () => {};

const defaultPermissions = { alert: true, badge: true, sound: true };

const manager = {
  getConstants: () => ({}),
  onFinishRemoteNotification: noop,
  setApplicationIconBadgeNumber: noop,
  getApplicationIconBadgeNumber: cb => {
    if (typeof cb === 'function') cb(0);
  },
  requestPermissions: async () => defaultPermissions,
  abandonPermissions: noop,
  checkPermissions: cb => {
    if (typeof cb === 'function') cb(defaultPermissions);
  },
  presentLocalNotification: noop,
  scheduleLocalNotification: noop,
  cancelAllLocalNotifications: noop,
  cancelLocalNotifications: noop,
  getInitialNotification: async () => null,
  getScheduledLocalNotifications: cb => {
    if (typeof cb === 'function') cb([]);
  },
  removeAllDeliveredNotifications: noop,
  removeDeliveredNotifications: noop,
  getDeliveredNotifications: cb => {
    if (typeof cb === 'function') cb([]);
  },
  getAuthorizationStatus: cb => {
    if (typeof cb === 'function') cb(0);
  },
  addListener: noop,
  removeListeners: noop,
};

module.exports = manager;
module.exports.default = manager;
