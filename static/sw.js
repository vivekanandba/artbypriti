// Art by Priti — service worker (spec 009).
//
// A gallery is a content site, not an app, and that changes the strategy.
//
// Nothing is precached beyond the manifest and the icons. Hugo fingerprints the
// stylesheet and script (/css/main.min.<hash>.css), so a hand-written precache
// list would name files that stop existing at the next deploy — and this worker
// is a static file, with no build step to substitute the hashes into it.
//
// Instead the worker caches what the visitor actually loaded. That also fixes the
// deploy problem by construction: a page and the exact CSS it references are
// cached together on the same visit, so they can never be a version apart.
//
// Images are deliberately NOT cached. The gallery is 566 MB of artwork; filling a
// phone's storage to make an offline visit prettier is a bad trade.
const CACHE = "artbypriti-v1";
const SHELL = ["/", "/manifest.webmanifest", "/images/icon-192.png", "/images/icon-512.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))),
  );
  self.clients.claim();
});

// Cacheable: the document and the things it needs to render. Not images.
const CACHEABLE = new Set(["document", "style", "script", "font", "manifest"]);

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (!CACHEABLE.has(request.destination)) return;
  // Network first: a cached page must never be shown when the real one is
  // reachable, or a new painting would be invisible to a returning visitor.
  event.respondWith(
    fetch(request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE).then((cache) => cache.put(request, copy));
        return response;
      })
      .catch(() => caches.match(request).then((cached) => cached || caches.match("/"))),
  );
});
