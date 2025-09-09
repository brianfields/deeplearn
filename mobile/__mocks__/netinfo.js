// Mock for @react-native-community/netinfo
const netInfoMock = {
  addEventListener: jest.fn(() => jest.fn()), // Returns unsubscribe function
  fetch: jest.fn(() =>
    Promise.resolve({
      isConnected: true,
      type: 'wifi',
      isInternetReachable: true,
    })
  ),
};

module.exports = netInfoMock;
module.exports.default = netInfoMock;
