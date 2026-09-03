/* Cache complet a la premiere visite : l'app doit fonctionner en mode avion. */
const CACHE = "inde-2026-v2";
const SOCLE = ["./", "./index.html", "./manifest.json",
               "./donnees/voyage.json", "./donnees/fond.json",
               "./donnees/prive.json"];

self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await c.addAll(SOCLE);
    // les photos sont ajoutees une par une : une seule manquante ne doit pas
    // faire echouer toute l'installation
    try {
      const d = await (await fetch("./donnees/voyage.json")).json();
      const imgs = [...new Set([...d.villes, ...d.activites]
        .map(x => x.photo).filter(Boolean))];
      await Promise.all(imgs.map(u => c.add(u).catch(() => {})));
    } catch (_) {}
    self.skipWaiting();
  })());
});

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
    self.clients.claim();
  })());
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const u = new URL(e.request.url);
  if (u.origin !== location.origin) return;      // Google Maps, liens externes
  e.respondWith((async () => {
    const hit = await caches.match(e.request);
    if (hit) {
      // rafraichissement silencieux en arriere-plan
      fetch(e.request).then(r => {
        if (r.ok) caches.open(CACHE).then(c => c.put(e.request, r));
      }).catch(() => {});
      return hit;
    }
    try {
      const r = await fetch(e.request);
      if (r.ok) (await caches.open(CACHE)).put(e.request, r.clone());
      return r;
    } catch (_) {
      return (await caches.match("./index.html")) || Response.error();
    }
  })());
});
