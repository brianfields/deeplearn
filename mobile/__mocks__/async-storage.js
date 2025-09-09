// Mock for @react-native-async-storage/async-storage
const mockStorage = {};

module.exports = {
  getItem: jest.fn(key => Promise.resolve(mockStorage[key] || null)),
  setItem: jest.fn((key, value) => {
    mockStorage[key] = value;
    return Promise.resolve();
  }),
  removeItem: jest.fn(key => {
    delete mockStorage[key];
    return Promise.resolve();
  }),
  getAllKeys: jest.fn(() => Promise.resolve(Object.keys(mockStorage))),
  multiRemove: jest.fn(keys => {
    keys.forEach(key => delete mockStorage[key]);
    return Promise.resolve();
  }),
  clear: jest.fn(() => {
    Object.keys(mockStorage).forEach(key => delete mockStorage[key]);
    return Promise.resolve();
  }),
};
