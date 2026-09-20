/* Remote Deck service worker — minimal shell.
 * No fetch caching: this is a live remote-control app, so stale assets would
 * be worse than no cache. Only registers on secure origins (e.g. localhost). */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());
