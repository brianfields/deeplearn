module.exports = new Proxy(
  {},
  {
    get: () => () => {},
    apply: () => {},
    has: () => true,
  }
);
