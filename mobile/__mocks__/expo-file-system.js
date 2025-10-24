const files = new Map();
const directories = new Set();

function normalizeUri(uri) {
  return uri.replace(/\\/g, '/');
}

function ensureParentDirectory(uri) {
  const normalized = normalizeUri(uri);
  const lastSlash = normalized.lastIndexOf('/');
  if (lastSlash === -1) {
    return '';
  }
  return normalized.slice(0, lastSlash);
}

module.exports = {
  documentDirectory: 'file://mock-documents/',

  __reset() {
    files.clear();
    directories.clear();
  },

  async getInfoAsync(uri) {
    const normalized = normalizeUri(uri);
    if (files.has(normalized)) {
      const entry = files.get(normalized);
      return {
        exists: true,
        uri: normalized,
        size: entry.size,
        modificationTime: entry.modificationTime,
      };
    }
    if (directories.has(normalized)) {
      return { exists: true, uri: normalized, isDirectory: true };
    }
    return { exists: false };
  },

  async makeDirectoryAsync(uri, options = {}) {
    const normalized = normalizeUri(uri);
    if (!directories.has(normalized)) {
      directories.add(normalized);
    }
    if (options.intermediates) {
      let parent = ensureParentDirectory(normalized);
      while (parent && !directories.has(parent)) {
        directories.add(parent);
        parent = ensureParentDirectory(parent);
      }
    }
  },

  async deleteAsync(uri) {
    const normalized = normalizeUri(uri);
    files.delete(normalized);
  },

  async downloadAsync(remoteUri, fileUri) {
    const normalized = normalizeUri(fileUri);
    const parent = ensureParentDirectory(normalized);
    if (parent) {
      directories.add(parent);
    }
    const now = Date.now();
    const fakeContent = `downloaded:${remoteUri}`;
    files.set(normalized, {
      size: fakeContent.length,
      modificationTime: now,
    });
    return {
      uri: normalized,
      status: 200,
      headers: {},
      bytesWritten: fakeContent.length,
    };
  },
};
