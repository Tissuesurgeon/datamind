/**
 * Web stub for @react-native-async-storage/async-storage.
 * @metamask/sdk pulls this in via @wagmi/connectors; it is not needed in the browser.
 */
const mem = new Map();

const AsyncStorage = {
  getItem: async (key) => (mem.has(key) ? mem.get(key) : null),
  setItem: async (key, value) => {
    mem.set(key, String(value));
  },
  removeItem: async (key) => {
    mem.delete(key);
  },
  clear: async () => {
    mem.clear();
  },
  getAllKeys: async () => [...mem.keys()],
  multiGet: async (keys) => keys.map((k) => [k, mem.get(k) ?? null]),
  multiSet: async (pairs) => {
    for (const [k, v] of pairs) mem.set(k, String(v));
  },
  multiRemove: async (keys) => {
    for (const k of keys) mem.delete(k);
  },
};

module.exports = AsyncStorage;
module.exports.default = AsyncStorage;
