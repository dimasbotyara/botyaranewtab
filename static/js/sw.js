/* Service Worker for Offline New Tab */
// Bump this when static assets change: assets are served stale-while-revalidate,
// so a new version tag is what guarantees the updated files win.
const CACHE_NAME = 'botyaranewtab-v3';
const STATIC_ASSETS = [
    '/',
    '/manifest.json',
    '/static/css/fonts.css',
    '/static/css/base.css',
    '/static/css/controls.css',
    '/static/css/background.css',
    '/static/css/layout.css',
    '/static/css/clock.css',
    '/static/css/search.css',
    '/static/css/shortcuts.css',
    '/static/css/widgets.css',
    '/static/css/settings.css',
    '/static/css/effects.css',
    '/static/css/hotkeys.css',
    '/static/css/utilities.css',
    '/static/js/utils.js',
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
    const request = event.request;

    // Only GET requests are cacheable; never cache API responses
    if (request.method !== 'GET' || request.url.includes('/api/') || request.url.includes('/sw.js')) {
        return;
    }

    // Stale-while-revalidate: instant render from cache, fresh copy next load
    event.respondWith(
        caches.match(request).then((cached) => {
            const network = fetch(request).then((response) => {
                if (response && response.ok && response.type === 'basic') {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                }
                return response;
            }).catch(() => cached);

            if (cached) {
                // Refresh in the background, don't block the paint
                event.waitUntil(network.catch(() => {}));
                return cached;
            }
            return network;
        }).catch(() => caches.match('/'))
    );
});
