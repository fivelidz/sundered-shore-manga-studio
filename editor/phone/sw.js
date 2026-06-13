// Service worker for the Panel Reviewer PWA.
// Caches the APP SHELL only (offline launch + home-screen install). It must NEVER
// cache /api/ responses (review state must be live) and uses network-first for
// /episodes/ renders so freshly generated variants always appear.

const SHELL = 'panels-shell-v1';
const ASSETS = [
  './', './index.html', './phone.css', './phone.js',
  './manifest.webmanifest', './icon.svg'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== SHELL).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Never intercept API — always go to network so state is correct.
  if (url.pathname.startsWith('/api/')) return;
  // Renders: network-first (new variants), fall back to cache if offline.
  if (url.pathname.startsWith('/episodes/')) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }
  // App shell: cache-first.
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
