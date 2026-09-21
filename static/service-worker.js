const CACHE_NAME = 'como-en-casa-v7';
const urlsToCache = [
  '/static/style.css',
  '/static/manifest.json',
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
  // Solo maneja GET
  if (event.request.method !== 'GET') return;

  // 🔥 NO cachear HTML ni JSON - siempre desde el servidor
  const url = event.request.url;
  if (url.endsWith('/') || url.includes('/admin') || url.includes('/chat') || url.includes('/pedido')) {
    return; // Deja pasar la petición al servidor directamente
  }

  // Para CSS, imágenes, etc → red primero, caché como fallback
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Actualiza el caché con la versión nueva
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return response;
      })
      .catch(() => {
        // Si falla la red, usa el caché
        return caches.match(event.request);
      })
  );
});