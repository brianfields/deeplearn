// Mock for react-native
module.exports = {
  Platform: {
    OS: 'ios',
    select: jest.fn(obj => obj.ios || obj.default),
  },
  Dimensions: {
    get: jest.fn(() => ({
      width: 375,
      height: 812,
    })),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  },
  StyleSheet: {
    create: jest.fn(styles => styles),
    absoluteFill: {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
      position: 'absolute',
    },
    hairlineWidth: 0.5,
  },
  View: 'View',
  Text: 'Text',
  Image: 'Image',
  TouchableOpacity: 'TouchableOpacity',
  ActivityIndicator: 'ActivityIndicator',
};
