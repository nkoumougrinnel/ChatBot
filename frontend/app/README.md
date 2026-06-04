# SUP'ONE AI — Frontend React (PWA + Android)

Interface principale du chatbot SUP'PTIC : **React 19**, **Vite 8**, **PWA** et **APK Android** (Capacitor 7).

| Document | Contenu |
|----------|---------|
| [docs/GUIDE_COMPLET.md](../../docs/GUIDE_COMPLET.md) | Installation, backend, tests, déploiement |
| [docs/MOBILE.md](../../docs/MOBILE.md) | **APK Android** — build, réseau, dépannage |

---

## Interface

- Style **ChatGPT** : fil centré, messages utilisateur en pastille bleue, assistant en texte libre
- Thèmes **clair** / **sombre** (icône soleil/lune, stockage `supone-theme`)
- Suggestions, streaming Gen3, feedback like/dislike
- Ports par défaut : backend **8001**, Vite **5174**

---

## Démarrage rapide (web)

```powershell
# Terminal 1 — Backend
cd backend
$env:DEBUG="True"
python manage.py runserver 127.0.0.1:8001

# Terminal 2 — Frontend
cd frontend/app
npm install
npm run dev
```

Ouvrir **http://localhost:5174** — le proxy Vite envoie `/api/*` vers le port 8001.

---

## Variables d’environnement

Copier `.env.example` vers `.env` :

```powershell
copy .env.example .env
```

| Variable | Usage |
|----------|--------|
| `VITE_API_URL` | URL backend **sans slash final** ; figée au `npm run build` (obligatoire pour l’APK) |

En dev web, `VITE_API_URL` peut rester vide (proxy Vite).

---

## Build PWA (production web)

```powershell
npm run build
npm run preview
```

Déployer le dossier `dist/` (Netlify, Vercel, etc.) avec `VITE_API_URL` pointant vers le backend HTTPS.

---

## APK Android

**Prérequis :** Node.js 18+, **JDK 21**, Android SDK API 35.

```powershell
cd frontend/app
npm install

# Éditer .env — ex. production Railway ou http://10.0.2.2:8001 (émulateur)
npm run android:build
# ou : npm run android:build:win
```

APK : `android/app/build/outputs/apk/debug/app-debug.apk`

```powershell
adb install -r android\app\build\outputs\apk\debug\app-debug.apk
npm run android:open   # Android Studio
```

Détails (réseau, clavier, thèmes natifs, checklist) : **[docs/MOBILE.md](../../docs/MOBILE.md)**.

---

## Scripts npm

| Script | Description |
|--------|-------------|
| `dev` | Serveur de développement (5174) |
| `build` | Build production → `dist/` |
| `preview` | Prévisualisation du build |
| `cap:sync` | Build + synchronisation Capacitor Android |
| `android:build` | Sync + APK debug Gradle |
| `android:build:win` | Idem avec détection JDK 21 |
| `android:open` | Ouvre le projet Android Studio |

---

## Structure `src/`

```
src/
├── App.jsx              # Shell chat (web + natif)
├── hooks/
│   ├── useChat.js       # Messages, streaming, santé API
│   ├── useTheme.js      # Thème clair/sombre + barre de statut
│   ├── useNativeKeyboard.js
│   └── usePwaInstall.js
├── components/          # ChatHeader, Composer, MessageBubble, …
├── api/client.js        # Appels /api et /api/v2
└── utils/nativeChrome.js
```

---

## Tests backend (avec frontend)

```powershell
cd backend
python manage.py runserver 127.0.0.1:8001
# autre terminal :
python scripts/test_full_suite.py
```

---

*Club Informatique SUP'PTIC.*
