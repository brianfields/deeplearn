// Safe no-op shim for React Native's deprecated PushNotificationIOS module.
// Avoids constructing NativeEventEmitter or touching native bridges.

class PushNotificationIOSShim {
  static addEventListener() {
    return { remove: () => {} };
  }
  static removeEventListener() {}
  static requestPermissions() {
    return Promise.resolve({ alert: false, badge: false, sound: false });
  }
  static abandonPermissions() {}
  static checkPermissions(callback) {
    const perms = { alert: false, badge: false, sound: false };
    if (typeof callback === 'function') callback(perms);
    return Promise.resolve(perms);
  }
  static getInitialNotification() {
    return Promise.resolve(null);
  }
  static presentLocalNotification() {}
  static scheduleLocalNotification() {}
  static cancelLocalNotifications() {}
  static cancelAllLocalNotifications() {}
  static getScheduledLocalNotifications(callback) {
    if (typeof callback === 'function') callback([]);
    return Promise.resolve([]);
  }
  static getDeliveredNotifications(callback) {
    if (typeof callback === 'function') callback([]);
    return Promise.resolve([]);
  }
  static removeDeliveredNotifications() {}
  static setApplicationIconBadgeNumber() {}
}

module.exports = PushNotificationIOSShim;
module.exports.default = PushNotificationIOSShim;
// eslint-disable-next-line @typescript-eslint/no-require-imports
const manager = require('./nativePushNotificationManagerIOS');
const noop = () => {};
const defaultPermissions = { alert: true, badge: true, sound: true };

const PushNotificationIOS = {
  addEventListener: noop,
  removeEventListener: noop,
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
  setApplicationIconBadgeNumber: manager.setApplicationIconBadgeNumber,
  getApplicationIconBadgeNumber: manager.getApplicationIconBadgeNumber,
  getAuthorizationStatus: cb => {
    if (typeof cb === 'function') cb(0);
  },
};

PushNotificationIOS.FetchResult = {
  NewData: 'UIBackgroundFetchResultNewData',
  NoData: 'UIBackgroundFetchResultNoData',
  ResultFailed: 'UIBackgroundFetchResultFailed',
};

PushNotificationIOS.Permissions = defaultPermissions;

module.exports = PushNotificationIOS;
module.exports.default = PushNotificationIOS;
