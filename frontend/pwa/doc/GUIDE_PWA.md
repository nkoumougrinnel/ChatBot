# 📱 Guide PWA - SUP'ONE AI

## 🎯 Qu'est-ce qu'une PWA ?

Une **Progressive Web App (PWA)** est une application web qui peut être installée sur n'importe quel appareil et qui fonctionne comme une application native. Votre chatbot SUP'ONE AI peut maintenant :

✅ Être installé sur l'écran d'accueil (mobile et desktop)  
✅ Fonctionner hors ligne (mode offline limité)  
✅ Recevoir des notifications push (optionnel)  
✅ Se lancer en plein écran sans barre d'adresse  
✅ Se mettre à jour automatiquement

---

## 📦 Fichiers PWA Créés

### Fichiers Principaux

| Fichier             | Description                                     | Obligatoire   |
| ------------------- | ----------------------------------------------- | ------------- |
| `manifest.json`     | Configuration de la PWA (nom, icônes, couleurs) | ✅ Oui        |
| `service-worker.js` | Gestion du cache et mode offline                | ✅ Oui        |
| `pwa.js`            | Script d'installation et de mise à jour         | ✅ Oui        |
| `pwa-styles.css`    | Styles pour bannières PWA                       | ✅ Oui        |
| `offline.html`      | Page affichée quand hors ligne                  | ⚠️ Recommandé |
| `index.html`        | HTML mis à jour avec support PWA                | ✅ Oui        |

### Structure des Dossiers

```
votre-projet/
├── frontend/
│   ├── index.html                 # landing minimal vers /pwa/index.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── main.js
│   └── pwa/
│       ├── index.html
│       ├── manifest.json
│       ├── service-worker.js
│       ├── js/
│       │   └── pwa.js
│       ├── css/
│       │   └── pwa-styles.css
│       ├── offline.html
│       ├── demo.html
│       └── icons/
│           ├── icone.png
│           ├── icon-72x72.png
│           └── ...
```

---

## 🚀 Installation (5 minutes)

### Étape 1: Copier les Fichiers (structure PWA indépendante)

```bash
# Copier/placer les fichiers dans le dossier PWA
cp frontend/pwa/manifest.json frontend/pwa/
cp frontend/pwa/service-worker.js frontend/pwa/
cp frontend/pwa/js/pwa.js frontend/pwa/js/
cp frontend/pwa/css/pwa-styles.css frontend/pwa/css/
cp frontend/pwa/offline.html frontend/pwa/
cp frontend/pwa/index.html frontend/pwa/  # point vers le site PWA
```

> Astuce : `frontend/index.html` est une page de redirection vers `/pwa/index.html`.

### Étape 2: Importer le CSS PWA

Dans votre fichier `styles.css`, ajoutez tout à la fin :

```css
/* Import des styles PWA */
@import url("pwa-styles.css");
```

**OU** copiez directement le contenu de `pwa-styles.css` à la fin de `styles.css`.

### Étape 3: Créer les Icônes

Vous devez générer plusieurs tailles d'icônes à partir de votre `icone.png`.

**Option A : Outil en ligne (Recommandé)**

1. Aller sur https://www.pwabuilder.com/imageGenerator
2. Uploader `icone.png`
3. Télécharger le pack d'icônes généré
4. Extraire dans `icons/`

**Option B : Avec ImageMagick (CLI)**

```bash
# Créer le dossier
mkdir -p icons

# Générer toutes les tailles
convert icone.png -resize 72x72 icons/icon-72x72.png
convert icone.png -resize 96x96 icons/icon-96x96.png
convert icone.png -resize 128x128 icons/icon-128x128.png
convert icone.png -resize 144x144 icons/icon-144x144.png
convert icone.png -resize 152x152 icons/icon-152x152.png
convert icone.png -resize 192x192 icons/icon-192x192.png
convert icone.png -resize 384x384 icons/icon-384x384.png
convert icone.png -resize 512x512 icons/icon-512x512.png
```

**Option C : Manuellement**

Si vous n'avez pas les icônes, commentez les lignes dans `manifest.json` :

```json
"icons": [
  {
    "src": "icone.png",
    "sizes": "192x192",
    "type": "image/png",
    "purpose": "any maskable"
  }
]
```

### Étape 4: Tester en Local

```bash
# Utiliser un serveur HTTP local
# Python 3
python -m http.server 8000

# Node.js
npx http-server -p 8000

# OU avec VS Code Live Server
```

Accéder à http://localhost:8000

---

## ✅ Vérification PWA

### 1. Chrome DevTools

1. Ouvrir DevTools (F12)
2. Aller dans l'onglet **Application**
3. Vérifier :
   - ✅ **Manifest** : Toutes les infos sont correctes
   - ✅ **Service Workers** : Status "Activated and Running"
   - ✅ **Cache Storage** : Ressources mises en cache

### 2. Lighthouse Audit

1. DevTools → Onglet **Lighthouse**
2. Cocher **Progressive Web App**
3. Cliquer **Generate report**
4. Score cible : **≥ 90/100**

### 3. Test d'Installation

**Desktop (Chrome/Edge)**

- Icône "Installer" dans la barre d'adresse
- OU bannière d'installation en haut de page

**Mobile (Android)**

- Menu → "Ajouter à l'écran d'accueil"
- OU bannière automatique après quelques visites

**Mobile (iOS)**

- Safari → Bouton Partager → "Sur l'écran d'accueil"
- ⚠️ Pas de bannière automatique sur iOS

---

## 🎨 Personnalisation

### Modifier les Couleurs

Dans `manifest.json` :

```json
{
  "theme_color": "#1a4594", // Couleur de la barre d'état
  "background_color": "#0a1628" // Couleur splash screen
}
```

### Modifier le Nom

```json
{
  "name": "SUP'ONE AI - Assistant Intelligent", // Nom complet
  "short_name": "SUP'ONE AI" // Nom court (écran d'accueil)
}
```

### Ajuster le Cache

Dans `frontend/pwa/service-worker.js`, ligne 6-7 :

```javascript
const CACHE_NAME = "supone-ai-v1"; // Changer version pour forcer MAJ
```

Ajouter plus de ressources à mettre en cache :

```javascript
const PRECACHE_URLS = [
  "/pwa/",
  "/pwa/index.html",
  "/pwa/styles.css",
  "/pwa/js/main.js",
  "/pwa/icons/icone.png",
  "/pwa/manifest.json",
  "/pwa/mon-autre-fichier.js", // ← Ajouter ici
];
```

---

## 🔧 Fonctionnalités Avancées

### 1. Notifications Push (Optionnel)

Le Service Worker est déjà configuré pour les notifications. Pour les activer :

```javascript
// Dans main.js ou pwa.js
async function requestNotificationPermission() {
  const permission = await Notification.requestPermission();

  if (permission === "granted") {
    console.log("✅ Notifications activées");
  }
}

// Appeler au bon moment (après une interaction utilisateur)
```

### 2. Mode Offline Avancé

Pour stocker les conversations hors ligne :

```javascript
// Dans service-worker.js
self.addEventListener("fetch", (event) => {
  if (event.request.url.includes("/api/chatbot/")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Mettre en cache pour offline
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Retourner depuis le cache si offline
          return caches.match(event.request);
        }),
    );
  }
});
```

### 3. Synchronisation en Arrière-Plan

Pour envoyer les messages en attente quand la connexion revient :

```javascript
// Enregistrer une sync task
navigator.serviceWorker.ready.then((registration) => {
  return registration.sync.register("sync-messages");
});

// Dans service-worker.js
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-messages") {
    event.waitUntil(syncPendingMessages());
  }
});
```

---

## 📊 Statistiques PWA

### Mesurer l'Engagement

Ajouter Google Analytics dans `pwa.js` :

```javascript
// Installation
window.addEventListener("appinstalled", () => {
  gtag("event", "pwa_install", {
    event_category: "engagement",
    event_label: "PWA Installation",
  });
});

// Lancement
if (isPWA()) {
  gtag("event", "pwa_launch", {
    event_category: "engagement",
    event_label: "PWA Launch",
  });
}
```

---

## 🐛 Dépannage

### Service Worker ne s'enregistre pas

**Solution** :

```javascript
// Vérifier la console pour les erreurs
// Assurez-vous que le chemin est correct
navigator.serviceWorker.register("/pwa/service-worker.js");
```

### Icônes ne s'affichent pas

**Solution** :

- Vérifier que les chemins dans `manifest.json` sont corrects
- Icônes doivent être au format PNG
- Tailles minimales : 192x192 et 512x512

### Bannière d'installation ne s'affiche pas

**Raisons possibles** :

- PWA déjà installée
- Critères PWA non remplis (vérifier Lighthouse)
- Utilisateur a déjà refusé (localStorage)
- iOS ne supporte pas les bannières automatiques

### Cache ne se met pas à jour

**Solution** :

```javascript
// Changer la version dans service-worker.js
const CACHE_NAME = "supone-ai-v2"; // ← Incrémenter
```

### Mode offline ne fonctionne pas

**Vérifications** :

1. Service Worker activé (DevTools → Application)
2. Ressources en cache (Cache Storage)
3. Tester en désactivant le réseau dans DevTools

---

## 📱 Déploiement

### Netlify

```toml
# netlify.toml
[[headers]]
  for = "/pwa/service-worker.js"
  [headers.values]
    Cache-Control = "no-cache"

[[headers]]
  for = "/pwa/manifest.json"
  [headers.values]
    Content-Type = "application/manifest+json"
```

### Vercel

```json
// vercel.json
{
  "headers": [
    {
      "source": "/pwa/service-worker.js",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "no-cache"
        }
      ]
    }
  ]
}
```

---

## ✅ Checklist PWA

### Avant Déploiement

- [ ] Tous les fichiers PWA copiés
- [ ] `pwa-styles.css` importé dans `styles.css`
- [ ] Icônes générées (au moins 192x192 et 512x512)
- [ ] `manifest.json` personnalisé
- [ ] Service Worker testé en local
- [ ] Lighthouse score > 90
- [ ] Test d'installation (desktop + mobile)
- [ ] Mode offline testé

### Après Déploiement

- [ ] PWA installable en production
- [ ] Service Worker activé
- [ ] Cache fonctionne
- [ ] Bannière d'installation s'affiche
- [ ] Mode offline fonctionnel
- [ ] Analytics PWA configuré

---

## 🎯 Améliorations Futures

### Court Terme

- [ ] Ajouter plus de ressources au cache
- [ ] Optimiser la stratégie de cache
- [ ] Améliorer la page offline

### Moyen Terme

- [ ] Notifications push réelles
- [ ] Synchronisation en arrière-plan
- [ ] Mode dark/light persistant

### Long Terme

- [ ] Share Target API (partage vers l'app)
- [ ] File System Access API
- [ ] Shortcuts personnalisés

---

## 📚 Ressources

- [PWA Builder](https://www.pwabuilder.com/)
- [Google PWA Docs](https://web.dev/progressive-web-apps/)
- [Service Worker Cookbook](https://serviceworke.rs/)
- [Can I Use - PWA](https://caniuse.com/?search=pwa)

---

**Version** : 1.0  
**Date** : 2026-02-12  
**Auteur** : SUP'ONE AI Team

🚀 **Votre chatbot est maintenant une PWA installable !**
