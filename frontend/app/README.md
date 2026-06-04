# SUP'ONE AI — Frontend React (PWA)

Interface React moderne, installable sur **mobile** et **bureau**.

> Guide complet (déploiement Netlify/Vercel, CORS, APK, dépannage) : **[../../docs/GUIDE_COMPLET.md](../../docs/GUIDE_COMPLET.md)**

## Démarrage

```bash
# Terminal 1 — Backend
cd backend
$env:DEBUG="True"   # PowerShell
python manage.py runserver

# Terminal 2 — Frontend React
cd frontend/app
npm install
npm run dev
```

Ouvrir **http://localhost:5173** — les appels `/api/*` sont proxifiés vers le port 8000.

## Build production (PWA)

```bash
npm run build
npm run preview
```

Déployer le dossier `dist/` (Netlify, Vercel, etc.) et définir `VITE_API_URL` vers votre backend Railway.

## Installation

- **Chrome / Edge** : icône « Installer » dans la barre d’adresse ou bannière dans l’app
- **Android** : « Ajouter à l’écran d’accueil »
- **iOS Safari** : Partager → « Sur l’écran d’accueil »

## APK Android

Prérequis : **Node.js**, **JDK 17+**, **Android SDK** (Android Studio).

```powershell
cd frontend/app
npm install

# URL du backend (défaut : production Railway dans .env)
# Émulateur local : VITE_API_URL=http://10.0.2.2:8000
# Téléphone + PC même Wi-Fi : VITE_API_URL=http://IP_LAN:8000

npm run android:build
```

APK généré :

`frontend/app/android/app/build/outputs/apk/debug/app-debug.apk`

Ouvrir le projet Android : `npm run android:open`
