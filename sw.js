// Keeps the app itself available when the connection drops.
// Network first (so updates show up straight away), cached copy when offline.
// Map tiles are left to the browser's normal cache.
const CACHE = "hunt-editor-shell-v6";
const SHELL = ["./", "index.html", "capacitor.js", "lib/leaflet.js", "lib/leaflet.css", "lib/pmtiles.js", "lib/protomaps-leaflet.js", "manifest.webmanifest", "icon-192.png", "icon-512.png", "map/three-cities.pmtiles"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return r;
    }).catch(() => caches.match(e.request, {ignoreSearch: true}).then(m => m || caches.match("index.html")))
  );
});
