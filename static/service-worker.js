const CACHE_NAME = 'como-en-casa-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/manifest.json',
  '/static/logo.png',
  '/static/icon-192.png'
];

self.addEventListener('install', (event) => {
  console.log('✅ Service Worker instalando...');
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.all(
        urlsToCache.map(url =>
          cache.add(url).catch(err => console.log('No se pudo cachear:', url))
        )
      );
    })
  );
});

self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker activo');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Solo maneja GET (no POST)
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).catch(() => {
        // Si falla la red y es HTML, devuelve la home
        if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html')) {
          return caches.match('/');
        }
      });
    })
  );
});