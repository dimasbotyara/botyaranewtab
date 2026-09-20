/* Service Worker for Offline New Tab */
const CACHE_NAME = 'botyaranewtab-v1';
const STATIC_ASSETS = [
    '/',
'/manifest.json',
'/static/css/style.css',
'/static/js/app.js',
'/static/js/i18n.js',
'/static/js/themes.js',
'/static/js/background.js',
'/static/js/search.js',
'/static/js/shortcuts.js',
'/static/js/widgets.js',
'/static/js/settings.js',
'/static/js/hotkeys.js',
'/static/js/confetti.js',
'/static/js/toast.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // API calls bypass cache or fallback gracefully
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then((response) => {
                return caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, response.clone());
                    return response;
                });
            });
        }).catch(() => caches.match('/'))
    );
});
