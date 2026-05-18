/* ════════════════════════════════════════════════════════════════
 *  COCON — Service Worker
 *  Stratégie : cache-first pour le shell (HTML/CSS/JS/icons),
 *              network-first pour les appels API (/api/*).
 * ════════════════════════════════════════════════════════════════ */

const CACHE_NAME = 'cocon-v9';

const SHELL_ASSETS = [
  '/style.css',
  '/manifest.json',
  '/icons/favicon-32.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png',
];

/* ─── Install : précharge le shell ─────────────────────────────── */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

/* ─── Activate : nettoie les anciens caches ─────────────────────── */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

/* ─── Fetch : routing des requêtes ─────────────────────────────── */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignore les requêtes non-GET et les extensions Chrome
  if (request.method !== 'GET') return;
  if (!url.protocol.startsWith('http')) return;

  // JS / HTML → toujours le réseau (évite un app.js obsolète en cache)
  if (url.pathname === '/app.js' || url.pathname === '/style.css' || url.pathname === '/' || url.pathname.endsWith('.html')) {
    event.respondWith(fetch(request, { cache: 'no-store', credentials: 'same-origin' }));
    return;
  }

  // API → network-first (avec fallback silencieux si hors ligne)
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

  // Google Fonts / ressources externes → network only (pas de mise en cache)
  if (!url.origin.includes(self.location.origin)) return;

  // Shell assets → cache-first
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
