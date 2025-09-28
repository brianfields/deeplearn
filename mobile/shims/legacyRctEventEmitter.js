const noop = () => {};

module.exports = {
  addListener: noop,
  removeListeners: noop,
  removeAllListeners: noop,
  emit: noop,
  default: {
    addListener: noop,
    removeListeners: noop,
    removeAllListeners: noop,
    emit: noop,
  },
};
