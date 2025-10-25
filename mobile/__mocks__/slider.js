/**
 * Mock for @react-native-community/slider
 */

const React = require('react');

const Slider = React.forwardRef((props, ref) => {
  return React.createElement('Slider', { ...props, ref });
});

Slider.displayName = 'Slider';

module.exports = Slider;
module.exports.default = Slider;
