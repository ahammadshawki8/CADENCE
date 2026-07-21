/* Cadence service worker - app-shell caching for offline / installable PWA. */
const CACHE = "cadence-v7";
const SHELL = [
  "/", "/static/style.css", "/static/app.js", "/static/favicon.svg",
  "/static/icon-192.png", "/static/icon-512.png", "/static/examples.json",
  "/static/passages.json", "/manifest.webmanifest"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // Never cache API calls (screening, PDF) — always hit the network.
  if (e.request.method !== "GET" || url.pathname.startsWith("/api/")) return;
  e.respondWith(
    caches.match(e.request).then(cached =>
      cached || fetch(e.request).then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return resp;
      }).catch(() => caches.match("/"))
    )
  );
});
