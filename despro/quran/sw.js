const CACHE_NAME = 'quran-app-v2';
const PAGES_CACHE = 'quran-pages-v1';
const urlsToCache = [
  '/quran/',
  '/quran/index.html',
  '/quran/manifest.json',
  '/quran/ayat_map'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened main cache');
        return cache.addAll(urlsToCache);
      })
      .then(() => caches.open(PAGES_CACHE))  // Create pages cache for lazy loading
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== PAGES_CACHE) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - smart caching strategy
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // SVG Pages - Cache-first strategy (Lazy Loading - pages load on demand & cache forever offline)
  if (url.pathname.includes('/quran/pages/') && url.pathname.endsWith('.svg')) {
    event.respondWith(
      caches.open(PAGES_CACHE).then((cache) => {
        return cache.match(event.request).then((response) => {
          // Return cached version if available
          if (response) {
            console.log('Loading page from cache:', url.pathname);
            return response;
          }
          
          // Otherwise fetch and cache for offline use
          return fetch(event.request).then((response) => {
            if (response && response.status === 200) {
              cache.put(event.request, response.clone());
              console.log('Cached page:', url.pathname);
            }
            return response;
          }).catch(() => {
            // If offline and not cached
            return new Response('الصفحة غير متاحة بدون اتصال إنترنت', { 
              status: 503,
              statusText: 'Offline'
            });
          });
        });
      })
    );
    return;
  }
  
  // Other requests - Network first, then cache
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const responseToCache = response.clone();
        if (response.status === 200) {
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});
