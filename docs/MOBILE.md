# SUP'ONE AI — Application mobile Android

Guide de référence pour l’**APK Android** (Capacitor 7), l’interface type ChatGPT et la connexion au backend.

> Voir aussi : [GUIDE_COMPLET.md](GUIDE_COMPLET.md) (installation globale, backend, tests, déploiement).

---

## 1. Vue d’ensemble

| Élément | Détail |
|---------|--------|
| Code source UI | `frontend/app/src/` (React 19 + Vite) |
| Shell natif | Capacitor 7 — `frontend/app/android/` |
| Identifiant | `com.supptic.suponeai` |
| Nom affiché | SUP'ONE AI |
| Build web embarqué | `frontend/app/dist/` (généré par `npm run build`) |

L’APK embarque l’interface React (fil centré, bulles utilisateur bleues, thème **clair / sombre**). Les requêtes API partent vers l’URL définie dans `VITE_API_URL` **au moment du build** — pas modifiable après installation sans reconstruire l’APK.

---

## 2. Interface utilisateur

### Style ChatGPT

- Fil de discussion centré, fond adaptatif
- Messages utilisateur en pastille bleue SUP'PTIC (`#1a4594`)
- Réponses assistant en texte simple (sans carte)
- Zone de saisie type « prompt box » en bas
- Écran d’accueil : « Comment puis-je vous aider ? » + suggestions en pills

### Thèmes clair et sombre

- Bouton soleil / lune dans l’en-tête
- Préférence mémorisée (`localStorage` : `supone-theme`)
- Sur Android : barre de statut synchronisée avec le thème (`nativeChrome.js`)

### Comportements natifs

| Fonction | Web PWA | APK |
|----------|---------|-----|
| Bannière « Installer l’app » | Oui (navigateur) | Non |
| Bouton installer dans l’en-tête | Si navigateur compatible | Non |
| Safe areas (encoche, barre gestes) | Oui | Oui |
| Clavier virtuel | Navigateur | Offset via `@capacitor/keyboard` |
| Feedback like / dislike | Oui | Oui |

---

## 3. Prérequis (Windows)

| Outil | Version |
|-------|---------|
| Node.js | 18+ (20 LTS recommandé) |
| JDK | **21** (obligatoire pour Capacitor 7 / Gradle) |
| Android SDK | API **35** (Android Studio → SDK Manager) |

Variables d’environnement (session PowerShell) :

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:PATH = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
```

Vérifier :

```powershell
java -version    # doit afficher 21
adb version
```

---

## 4. Configurer l’URL du backend

Copier le modèle et éditer **avant** tout build APK :

```powershell
cd frontend\app
copy .env.example .env
notepad .env
```

| Scénario | `VITE_API_URL` |
|----------|----------------|
| Téléphone réel (recommandé) | `https://VOTRE-SERVICE.up.railway.app` |
| Émulateur + backend local PC | `http://10.0.2.2:8001` |
| Téléphone + PC même Wi-Fi | `http://192.168.x.x:8001` (IP LAN du PC) |

**Important :** `localhost` et `127.0.0.1` ne fonctionnent **pas** depuis un téléphone physique. Le trafic HTTP en clair est autorisé (`usesCleartextTraffic`, `network_security_config.xml`).

Après modification du `.env`, reconstruire :

```powershell
npm run build
npx cap sync android
```

---

## 5. Construire l’APK debug

```powershell
cd frontend\app
npm install
npm run android:build
```

Avec détection automatique du JDK Microsoft :

```powershell
npm run android:build:win
```

**Fichier produit :**

```
frontend/app/android/app/build/outputs/apk/debug/app-debug.apk
```

### Installer sur un appareil

```powershell
adb install -r frontend\app\android\app\build\outputs\apk\debug\app-debug.apk
```

Ou copier le `.apk` sur le téléphone (autoriser l’installation depuis sources inconnues).

### Ouvrir dans Android Studio

```powershell
npm run android:open
```

Puis **Run** sur un émulateur ou un appareil USB (débogage USB activé).

---

## 6. Développement avec backend local

**Terminal 1 — Backend**

```powershell
cd backend
$env:DEBUG="True"
python manage.py runserver 0.0.0.0:8001
```

Écouter sur `0.0.0.0` permet l’accès depuis le réseau local (téléphone ou `10.0.2.2`).

**Terminal 2 — Préparer l’APK pour l’émulateur**

```powershell
cd frontend\app
# .env : VITE_API_URL=http://10.0.2.2:8001
npm run android:build
adb install -r android\app\build\outputs\apk\debug\app-debug.apk
```

**Alternative — Dev web dans le navigateur du téléphone**

```powershell
npm run dev -- --host
```

Ouvrir `http://IP_DU_PC:5174` sur le même Wi-Fi (proxy API vers `:8001`).

---

## 7. Scripts npm utiles

| Script | Action |
|--------|--------|
| `npm run dev` | Vite dev server (port 5174) |
| `npm run build` | Build production → `dist/` |
| `npm run cap:sync` | `build` + `cap sync android` |
| `npm run android:build` | Sync + `assembleDebug` |
| `npm run android:build:win` | Idem + détection JDK 21 |
| `npm run android:open` | Ouvre le projet dans Android Studio |

---

## 8. Structure technique mobile

```
frontend/app/
├── capacitor.config.json    # Splash, StatusBar, Keyboard
├── src/
│   ├── main.jsx             # Splash, classe native-app
│   ├── hooks/
│   │   ├── useTheme.js      # Thème + barre de statut
│   │   └── useNativeKeyboard.js
│   └── utils/nativeChrome.js
└── android/
    ├── app/src/main/
    │   ├── AndroidManifest.xml
    │   └── res/xml/network_security_config.xml
    └── gradlew.bat
```

---

## 9. Dépannage APK

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| « Serveur inaccessible » | Mauvaise `VITE_API_URL` ou backend arrêté | Vérifier `.env`, rebuild, `curl` health |
| Pas de réponse Gen3 | Index / clé API absents | `python manage.py setup_gen3` sur le serveur |
| `phase1: indexing_required` | Vecteurs FAQ non calculés | `python manage.py rebuild_vectors` |
| Build Java échoue | JDK 8/17 ou absent | Installer JDK **21**, `JAVA_HOME` |
| Gradle SDK manquant | Platform 35 non installé | Android Studio → SDK Manager |
| CORS en production | Origine non autorisée | Ajouter domaine dans `CORS_ALLOWED_ORIGINS` |
| Chat OK sur web, KO sur APK | URL figée au build | Rebuild avec la bonne `VITE_API_URL` |

### Logs Android

```powershell
adb logcat | Select-String -Pattern "Capacitor|chromium"
```

---

## 10. APK release (Play Store)

1. Créer un keystore : `keytool -genkey -v -keystore supone-release.keystore ...`
2. Configurer la signature dans `android/app/build.gradle`
3. `cd android && .\gradlew.bat assembleRelease`
4. Publier via [Google Play Console](https://play.google.com/console)

Pour la production, utiliser **HTTPS** (`VITE_API_URL=https://...`) et un backend avec `DEBUG=False`, `SECRET_KEY` et CORS configurés.

---

## 11. Checklist avant distribution

- [ ] Backend accessible (`GET /api/health/` → `status: ok`)
- [ ] FAQ indexées (`phase1: ready`, ~11k entrées si import complet)
- [ ] `VITE_API_URL` HTTPS pour usage réel
- [ ] `npm run build` sans erreur
- [ ] `npm run android:build` réussi
- [ ] Test sur appareil : connexion, question, streaming, feedback, thème clair/sombre
- [ ] `.env` non commité (secrets / URL internes)

---

*Club Informatique SUP'PTIC — SUP'ONE AI.*
