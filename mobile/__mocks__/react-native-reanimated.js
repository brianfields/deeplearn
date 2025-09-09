// Mock for react-native-reanimated
module.exports = {
  useSharedValue: jest.fn(() => ({ value: 0 })),
  useAnimatedStyle: jest.fn(fn => fn()),
  withTiming: jest.fn(value => value),
  withSpring: jest.fn(value => value),
  Animated: {
    View: 'Animated.View',
  },
};
