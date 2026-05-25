/* MayaOS Service Worker v1 */
const CACHE = 'mayaos-v1';

const PRECACHE = [
  '/',
  '/index.html',
  '/index.tsx',
  '/mazkirah-page.html',
  '/icon-192.png',
  '/icon-512.png',
  '/manifest.json'
];

/* ── Install: pre-cache core assets ── */
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE).catch(() => {}))
  );
});

/* ── Activate: clean old caches ── */
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

/* ── Fetch: network-first, fallback to cache ── */
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  /* Always go to network for API calls & OAuth */
  if (
    url.hostname.includes('googleapis.com') ||
    url.hostname.includes('google.com') ||
    url.hostname.includes('accounts.google')
  ) {
    return; /* let browser handle normally */
  }

  e.respondWith(
    fetch(e.request)
      .then(res => {
        /* Cache a fresh copy of same-origin resources */
        if (res.ok && url.origin === self.location.origin) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request).then(r => r || caches.match('/')))
  );
});
