/* ════════════════════════════════════════════════════════════════
 *  COCON — Service Worker
 *  Shell (HTML/JS/CSS/SW) → réseau uniquement.
 *  Icônes / manifest → cache pour offline.
 * ════════════════════════════════════════════════════════════════ */

const CACHE_NAME = 'cocon-v10';

const OFFLINE_ASSETS = [
  '/manifest.json',
  '/icons/favicon-32.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png',
];

function isShellPath(pathname) {
  return (
    pathname === '/' ||
    pathname === '/index.html' ||
    pathname === '/app.js' ||
    pathname === '/style.css' ||
    pathname === '/sw.js'
  );
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (!url.protocol.startsWith('http')) return;

  // Shell : jamais de cache (évite une UI figée après deploy)
  if (isShellPath(url.pathname)) {
    event.respondWith(fetch(request, { cache: 'no-store', credentials: 'same-origin' }));
    return;
  }

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request, { credentials: 'same-origin' }).catch(() =>
        new Response(JSON.stringify({ error: 'hors ligne' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    );
    return;
  }

  if (!url.origin.includes(self.location.origin)) return;

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request, { credentials: 'same-origin' }).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      });
    })
  );
});
