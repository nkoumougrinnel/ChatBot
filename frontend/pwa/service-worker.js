// Service Worker pour SUP'ONE AI PWA
// Version 2.1.0 - Gestion stabilisée du mode hors ligne

const CACHE_NAME = "supone-ai-v2-1";
const RUNTIME_CACHE = "supone-ai-runtime-v2-1";

// Ressources à mettre en cache lors de l'installation
const PRECACHE_URLS = [
  "/pwa/",
  "/pwa/index.html",
  "/pwa/offline.html",
  "/pwa/demo.html",
  "/css/styles.css",
  "/js/main.js",
  "/pwa/js/pwa.js",
  "/pwa/css/pwa-styles.css",
  "/pwa/icons/icone.png",
  "/pwa/manifest.json",
  "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
];

// Installation du Service Worker
self.addEventListener("install", (event) => {
  console.log("[SW] Installation en cours...");

  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => {
        console.log("[SW] Mise en cache des ressources statiques");
        return cache
          .addAll(
            PRECACHE_URLS.map((url) => new Request(url, { cache: "reload" })),
          )
          .catch((error) => {
            console.warn(
              "[SW] Erreur lors du cache de certaines ressources:",
              error,
            );
            // Continuer même si certaines ressources échouent
            return Promise.resolve();
          });
      })
      .then(() => {
        console.log("[SW] Installation terminée");
        return self.skipWaiting();
      }),
  );
});

// Activation du Service Worker
self.addEventListener("activate", (event) => {
  console.log("[SW] Activation en cours...");

  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE;
            })
            .map((cacheName) => {
              console.log("[SW] Suppression du cache obsolète:", cacheName);
              return caches.delete(cacheName);
            }),
        );
      })
      .then(() => {
        console.log("[SW] Activation terminée");
        return self.clients.claim();
      }),
  );
});

// ✅ Stratégie de cache améliorée avec timeout pour éviter les blocages
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET
  if (request.method !== "GET") {
    return;
  }

  // ✅ TOUJOURS servir offline.html et demo.html depuis le cache (hors ligne garanti)
  if (
    url.pathname === "/pwa/offline.html" ||
    url.pathname === "/pwa/demo.html"
  ) {
    event.respondWith(
      caches.match(request).then((response) => {
        if (response) {
          console.log("[SW] Serving from cache (offline mode):", url.pathname);
          return response;
        }
        // Fallback: essayer le réseau si pas en cache
        console.warn("[SW] Page not in cache, trying network:", url.pathname);
        return fetch(request).catch(() => {
          // Si le réseau échoue aussi, générer une page d'erreur basique
          if (url.pathname === "/pwa/offline.html") {
            return new Response(generateOfflineHTML(), {
              headers: { "Content-Type": "text/html" },
            });
          }
          // Pour demo.html, rediriger vers offline.html
          return caches.match("/pwa/offline.html").then((offline) => {
            return (
              offline ||
              new Response(generateOfflineHTML(), {
                headers: { "Content-Type": "text/html" },
              })
            );
          });
        });
      }),
    );
    return;
  }

  // ✅ Stratégie améliorée pour les requêtes de navigation (pages HTML)
  if (request.mode === "navigate") {
    event.respondWith(
      // Essayer le réseau avec timeout de 5 secondes (plus généreux)
      fetchWithTimeout(request, 5000)
        .then((response) => {
          // Si succès, retourner la réponse
          if (response && response.ok) {
            console.log("[SW] Navigation online:", url.pathname);
            return response;
          }
          throw new Error("Response not ok");
        })
        .catch(async (error) => {
          console.log("[SW] Navigation offline détectée pour:", url.pathname);
          console.log("[SW] Erreur:", error.message);

          // Essayer de récupérer offline.html depuis le cache
          const offlinePage = await caches.match("/pwa/offline.html");
          if (offlinePage) {
            console.log("[SW] Serving offline.html from cache");
            return offlinePage;
          }

          // Fallback HTML si offline.html n'est pas en cache
          console.warn("[SW] offline.html not in cache, generating fallback");
          return new Response(generateOfflineHTML(), {
            headers: { "Content-Type": "text/html" },
          });
        }),
    );
    return;
  }

  // Ignorer les requêtes vers d'autres origines (sauf CDN)
  if (
    url.origin !== location.origin &&
    !url.href.includes("cdn.jsdelivr.net") &&
    !url.href.includes("cdnjs.cloudflare.com")
  ) {
    // Network First pour les API externes
    if (url.pathname.includes("/api/")) {
      event.respondWith(networkFirst(request));
      return;
    }
    return;
  }

  // API: Network First avec timeout
  if (url.pathname.includes("/api/")) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Assets statiques: Cache First
  if (
    request.destination === "style" ||
    request.destination === "script" ||
    request.destination === "image" ||
    request.destination === "font"
  ) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Par défaut: Network First avec timeout
  event.respondWith(networkFirst(request));
});

// ✅ Nouvelle fonction: Fetch avec timeout
function fetchWithTimeout(request, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error("Request timeout"));
    }, timeout);

    fetch(request)
      .then((response) => {
        clearTimeout(timeoutId);
        resolve(response);
      })
      .catch((error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
  });
}

// Stratégie Cache First
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  if (cached) {
    console.log("[SW] Cache hit:", request.url);
    // Mettre à jour le cache en arrière-plan sans bloquer
    fetchWithTimeout(request, 2000)
      .then((response) => {
        if (response && response.status === 200) {
          cache.put(request, response.clone());
        }
      })
      .catch(() => {
        // Ignorer les erreurs de mise à jour en arrière-plan
      });
    return cached;
  }

  try {
    const response = await fetchWithTimeout(request, 5000);

    if (response && response.status === 200) {
      const responseToCache = response.clone();
      cache.put(request, responseToCache);
    }

    return response;
  } catch (error) {
    console.error("[SW] Erreur fetch:", error);

    return new Response("Ressource non disponible hors ligne", {
      status: 503,
      statusText: "Service Unavailable",
      headers: new Headers({
        "Content-Type": "text/plain",
      }),
    });
  }
}

// Stratégie Network First avec timeout
async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);

  try {
    const response = await fetchWithTimeout(request, 5000);

    if (response && response.status === 200) {
      const responseToCache = response.clone();
      cache.put(request, responseToCache);
    }

    return response;
  } catch (error) {
    console.log("[SW] Réseau indisponible, utilisation du cache");

    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }

    // Pour les API, retourner une erreur JSON
    if (request.url.includes("/api/")) {
      return new Response(
        JSON.stringify({
          error:
            "Vous êtes hors ligne. Veuillez vérifier votre connexion internet.",
          offline: true,
        }),
        {
          status: 503,
          headers: new Headers({
            "Content-Type": "application/json",
          }),
        },
      );
    }

    return new Response("Contenu non disponible hors ligne", {
      status: 503,
      statusText: "Service Unavailable",
    });
  }
}

// ✅ Fonction pour générer la page offline HTML
function generateOfflineHTML() {
  return `<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hors ligne - SUP'ONE AI</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #0a1628 0%, #1a4594 100%);
      color: white;
      text-align: center;
      padding: 20px;
    }
    .container {
      max-width: 500px;
      animation: fadeIn 0.5s ease-in;
    }
    .icon {
      font-size: 64px;
      margin-bottom: 24px;
      opacity: 0.8;
    }
    h1 {
      font-size: 28px;
      margin-bottom: 16px;
      font-weight: 600;
    }
    p {
      opacity: 0.9;
      line-height: 1.6;
      font-size: 16px;
      margin-bottom: 24px;
    }
    button {
      padding: 14px 32px;
      background: white;
      color: #1a4594;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
    }
    button:active {
      transform: translateY(0);
    }
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    .status {
      margin-top: 32px;
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      font-size: 14px;
      opacity: 0.8;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="icon">📡</div>
    <h1>Vous êtes hors ligne</h1>
    <p>Impossible de se connecter au serveur. Veuillez vérifier votre connexion internet et réessayer.</p>
    <button onclick="window.location.reload()">Réessayer</button>
    <div class="status">
      Service Worker actif - Certaines fonctionnalités sont disponibles hors ligne
    </div>
  </div>
  <script>
    // Vérifier automatiquement la connexion toutes les 5 secondes
    setInterval(() => {
      if (navigator.onLine) {
        console.log('Connexion rétablie, rechargement...');
        window.location.reload();
      }
    }, 5000);
  </script>
</body>
</html>`;
}

// Notifications Push
self.addEventListener("push", (event) => {
  const options = {
    body: event.data ? event.data.text() : "Nouvelle notification",
    icon: "/icons/icone.png",
    badge: "/icons/icone.png",
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1,
    },
    actions: [
      {
        action: "explore",
        title: "Voir",
      },
      {
        action: "close",
        title: "Fermer",
      },
    ],
  };

  event.waitUntil(self.registration.showNotification("SUP'ONE AI", options));
});

// Gestion des clics sur les notifications
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "explore") {
    event.waitUntil(clients.openWindow("/"));
  }
});

// Synchronisation en arrière-plan
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-messages") {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  console.log("[SW] Synchronisation des messages...");
  // Logique de synchronisation
}

// Message du client
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }

  if (event.data && event.data.type === "CACHE_URLS") {
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(event.data.urls);
      }),
    );
  }
});

console.log("[SW] Service Worker chargé - Version 2.1.0 (Stabilisée)");
