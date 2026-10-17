const CACHE_NAME = 'remote-deck-v1.0.13';
const PRECACHE_ASSETS = [
  '/',
  '/static/css/tokens.css',
  '/static/css/tailwind.css',
  '/static/css/base.css',
  '/static/css/components.css',
  '/static/js/preset-logic.js',
  '/static/js/state.js',
  '/static/js/transport.js',
  '/static/js/media.js',
  '/static/socket.io.min.js',
  '/static/js/trackpad-logic.js',
  '/static/js/trackpad.js',
  '/static/js/presentation.js',
  '/static/js/app.js',
  '/static/icon.svg',
  '/static/manifest.webmanifest'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  let url;
  try {
    url = new URL(event.request.url);
  } catch {
    return;
  }
  // Only handle GET requests for static resources and main shell
  if (event.request.method !== 'GET' || url.pathname.startsWith('/socket.io') || url.pathname === '/ping' || url.pathname === '/qr.png') {
    return;
  }
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok && (url.pathname.startsWith('/static/') || url.pathname === '/')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
