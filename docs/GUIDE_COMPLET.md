# Guide complet — ChatBot SUP'ONE AI

Documentation d’exécution locale, de configuration, de tests et de déploiement du projet **ChatBot SUP'PTIC** (backend Django + frontends React/PWA + APK Android).

---

## Table des matières

1. [Vue d’ensemble](#1-vue-densemble)
2. [Prérequis](#2-prérequis)
3. [Structure du projet](#3-structure-du-projet)
4. [Installation locale](#4-installation-locale)
5. [Configuration](#5-configuration)
6. [Initialisation des données](#6-initialisation-des-données)
7. [Exécution en développement](#7-exécution-en-développement)
8. [Tests](#8-tests)
9. [API REST](#9-api-rest)
10. [Déploiement backend (Railway)](#10-déploiement-backend-railway)
11. [Déploiement frontend (PWA / site statique)](#11-déploiement-frontend-pwa--site-statique)
    - Guide détaillé pas à pas : **[DEPLOIEMENT.md](DEPLOIEMENT.md)**
12. [APK Android (Capacitor)](#12-apk-android-capacitor)
13. [Dépannage](#13-dépannage)
14. [Checklist production](#14-checklist-production)

---

## 1. Vue d’ensemble

Le projet est un assistant FAQ pour **SUP'PTIC** avec deux pipelines de réponse :

| Pipeline | Préfixe API | Technologie | Rôle |
|----------|-------------|-------------|------|
| **Phase 1** | `/api/` | TF-IDF + cosinus sur la base FAQ Django | Toujours disponible si les vecteurs sont indexés |
| **Gen3 (RAG)** | `/api/v2/` | Règles → FAISS (MiniLM) → repli TF-IDF → Gemini | Optionnel ; nécessite dépendances + index + clé API |

**Frontends disponibles :**

| Dossier | Technologie | Usage recommandé |
|---------|-------------|------------------|
| `frontend/app/` | React 19 + Vite + PWA + Capacitor | **Principal** — web, mobile installable, APK |
| `frontend/advanced_chat/` | HTML/JS vanilla + PWA | Version historique |
| `frontend/` (racine) | HTML simple | Redirection / démo minimale |

### Interface React (`frontend/app`)

- Layout type **ChatGPT** : fil centré, composer en bas, suggestions en pills
- Thèmes **clair** et **sombre** (bouton dans l’en-tête, préférence mémorisée)
- Palette SUP'PTIC (`#1a4594`, fond sombre `#070f1f`)
- Pas d’affichage technique (méthode, score, latence) dans le chat
- Feedback discret (pouce haut / bas + commentaire optionnel)
- **APK Android** : même UI, barre de statut adaptée au thème, gestion clavier — voir **[MOBILE.md](MOBILE.md)**

---

## 2. Prérequis

### Backend

| Outil | Version minimale | Notes |
|-------|------------------|-------|
| Python | 3.10+ (3.13 supporté) | Voir `backend/runtime.txt` |
| pip + venv | récent | Environnement virtuel recommandé |
| (Optionnel) PostgreSQL | 14+ | Production ; SQLite suffit en local |

### Frontend React (`frontend/app`)

| Outil | Version minimale |
|-------|------------------|
| Node.js | 18+ (20 LTS recommandé) |
| npm | 9+ |

### APK Android

| Outil | Version |
|-------|---------|
| JDK | **21** (Microsoft OpenJDK ou Android Studio JBR) |
| Android SDK | API 35 (installé via Android Studio) |
| Gradle | fourni par le wrapper du projet |

### Services externes (optionnels)

- **Google Gemini** : [clé API](https://aistudio.google.com/app/apikey) pour le niveau LLM du Gen3
- **Railway** (ou autre PaaS) : hébergement backend
- **Netlify / Vercel** : hébergement frontend statique

---

## 3. Structure du projet

```
ChatBot/
├── .env.example              # Modèle variables backend (racine)
├── requirements.txt          # Dépendances Python (canonique, déploiement)
├── railway.json              # Déploiement Railway (healthcheck, start)
├── nixpacks.toml             # Build Python 3.13 sur Railway
├── deploy/                   # Modèles de variables (Docker, Railway, Netlify)
├── docker-compose.yml        # Déploiement serveur (Postgres + API + Nginx)
├── docker/                   # Dockerfiles et config Nginx
├── .github/workflows/ci.yml  # Tests backend + build frontend
│
├── backend/
│   ├── config/               # settings.py, urls.py, wsgi
│   ├── faq/                  # Modèles FAQ, API Phase 1, /api/health/
│   ├── chatbot/              # TF-IDF, engine/ (Gen3), commandes management
│   ├── users/                # Utilisateur personnalisé
│   ├── rag_data/             # Index FAISS + métadonnées (généré)
│   ├── data/                 # JSON règles conversationnelles
│   └── manage.py
│
├── frontend/
│   ├── app/                  # React + Vite + Capacitor (recommandé)
│   │   ├── .env.example      # VITE_API_URL pour build/APK
│   │   └── android/          # Projet Android (APK)
│   ├── advanced_chat/        # PWA vanilla historique
│   └── index.html            # Démo simple
│
└── docs/
    ├── GUIDE_COMPLET.md        # Ce document
    ├── MOBILE.md               # APK Android, thèmes, dépannage mobile
    └── backend/                # Docs techniques détaillées
```

---

## 4. Installation locale

### 4.1 Cloner le dépôt

```powershell
git clone <url-du-depot>
cd ChatBot
```

### 4.2 Environnement Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux / macOS :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4.3 Installer les dépendances backend

```powershell
pip install -r requirements.txt
```

> **Durée** : l’installation peut prendre plusieurs minutes (spaCy, scikit-learn, sentence-transformers, FAISS).

### 4.4 Configurer l’environnement

```powershell
copy .env.example .env
# ou copier aussi dans backend/ :
copy .env.example backend\.env
```

Éditez `.env` (voir [section 5](#5-configuration)).

### 4.5 Initialiser le backend

```powershell
cd backend
python manage.py setup_demo
```

Cette commande exécute : migrations → fixtures FAQ de démo → indexation TF-IDF Phase 1.

### 4.6 (Optionnel) Activer le pipeline Gen3

```powershell
# Ajouter GEMINI_API_KEY dans .env pour le LLM
python manage.py setup_gen3 --allow-download
python manage.py check_gen3
```

### 4.7 Installer le frontend React

```powershell
cd ..\frontend\app
npm install
```

---

## 5. Configuration

Django charge `.env` depuis **`backend/.env`** puis **la racine du projet** (`.env`).

### 5.1 Variables backend (`.env`)

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `SECRET_KEY` | **Oui** en prod (`DEBUG=False`) | Clé Django. Génération : `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | — | `True` en dev, `False` en production |
| `ALLOWED_HOSTS` | Prod | Hôtes séparés par virgules. Sous-domaine Railway : `.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | Prod | URLs frontend HTTPS, ex. `https://votre-app.netlify.app` |
| `DATABASE_URL` | Prod recommandé | Postgres : `postgres://user:pass@host:5432/db` ; vide = SQLite local |
| `GEMINI_API_KEY` | Gen3 LLM | Active la génération Gemini |
| `GEMINI_MODEL` | — | Défaut : `gemini-2.0-flash` |
| `HF_OFFLINE` | — | `1` (défaut) : pas de téléchargement HuggingFace au runtime |

**Exemple développement** (`.env` à la racine ou dans `backend/`) :

```env
SECRET_KEY=dev-only-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5174,http://127.0.0.1:5174
DATABASE_URL=
GEMINI_API_KEY=
HF_OFFLINE=1
```

**Exemple production Railway** :

```env
SECRET_KEY=<cle-aleatoire-longue>
DEBUG=False
ALLOWED_HOSTS=.up.railway.app,votre-service.up.railway.app
CORS_ALLOWED_ORIGINS=https://votre-frontend.netlify.app
DATABASE_URL=postgres://...
GEMINI_API_KEY=<votre-cle-gemini>
HF_OFFLINE=1
```

### 5.2 Variables frontend (`frontend/app/.env`)

Utilisées au **build** Vite (`npm run build`, APK).

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | URL du backend **sans slash final** |

Exemples :

```env
# Production (téléphone réel, Netlify, APK)
VITE_API_URL=https://chatbot-production-5202.up.railway.app

# Émulateur Android + backend local sur PC
VITE_API_URL=http://10.0.2.2:8001

# Téléphone physique + backend sur le même Wi-Fi
VITE_API_URL=http://192.168.1.42:8001

# Dev Vite : laisser vide ou ne pas définir — le proxy `/api` → :8001 suffit
```

Copier le modèle :

```powershell
cd frontend\app
copy .env.example .env
```

---

## 6. Initialisation des données

### Commandes Django utiles

| Commande | Description |
|----------|-------------|
| `python manage.py migrate` | Applique les migrations |
| `python manage.py setup_demo` | Migrations + fixtures + vecteurs TF-IDF Phase 1 |
| `python manage.py rebuild_vectors` | Recalcule les vecteurs FAQ Phase 1 |
| `python manage.py build_rag_index` | Construit `rag_data/index.bin` (FAISS) |
| `python manage.py setup_gen3` | `setup_demo` + index FAISS + cache TF-IDF Gen3 |
| `python manage.py setup_gen3 --allow-download` | Idem + télécharge MiniLM si absent |
| `python manage.py check_gen3` | Diagnostic FAISS / TF-IDF / Gemini |
| `python manage.py createsuperuser` | Compte admin Django |

### Vérifier que tout fonctionne

```powershell
cd backend
python manage.py runserver 127.0.0.1:8001
```

Dans un autre terminal :

```powershell
curl http://127.0.0.1:8001/api/health/
```

Réponse attendue (extrait) :

```json
{
  "status": "ok",
  "phase1": "ready",
  "gen3": { "available": true }
}
```

Si `phase1` vaut `indexing_required` : exécutez `python manage.py rebuild_vectors` ou `setup_demo`.

---

## 7. Exécution en développement

### Scénario recommandé (React + backend)

**Terminal 1 — Backend**

```powershell
cd backend
$env:DEBUG="True"
python manage.py runserver 127.0.0.1:8001
```

**Terminal 2 — Frontend React**

```powershell
cd frontend\app
npm run dev
```

Ouvrir : **http://localhost:5174**

Le proxy Vite redirige `/api/*` vers `http://127.0.0.1:8001` (voir `frontend/app/vite.config.js`).

### Autres frontends

**PWA vanilla** : servir `frontend/advanced_chat/` (Live Server, `npx serve`, etc.) et pointer l’API vers `:8001` (voir `main.js`).

**Preview build production** :

```powershell
cd frontend\app
npm run build
npm run preview
```

→ http://localhost:4174 (proxy API identique au dev).

### Admin Django

http://127.0.0.1:8001/admin/ — créer un superutilisateur avec `createsuperuser` si besoin.

---

## 8. Tests

### Tests unitaires Django

```powershell
cd backend
python manage.py test
```

Couverture : modèles FAQ, feedback, endpoints Phase 1, recherche chatbot.

### Suite complète (Gen3 + feedback + Phase 1)

Backend démarré sur **8001**, puis :

```powershell
cd backend
python scripts/test_full_suite.py
```

Vérifie notamment : réponses cohérentes (inscription, frais, localisation), feedback like/dislike, endpoints Phase 1.

### Test manuel du pipeline Gen3

```powershell
python backend\scripts\test_pipeline_api.py
```

(Backend doit tourner sur le port 8001.)

### Import FAQ depuis JSON

```powershell
cd backend
python manage.py import_faq_json
python manage.py rebuild_vectors
python manage.py setup_gen3 --allow-download
```

Le script `load_json_data.py` ignore automatiquement `conversational_rules.json` (format non FAQ).

---

## 9. API REST

### Phase 1 — `/api/`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/health/` | Santé backend, FAQ, Gen3 |
| `POST` | `/api/chatbot/ask/` | Question → résultats TF-IDF (`top_k`) |
| `GET` | `/api/faq/` | Liste FAQ (paginée) |
| `GET` | `/api/categories/` | Catégories |
| `POST` | `/api/feedback/` | Like / dislike |
| `GET` | `/api/stats/` | Statistiques / suggestions populaires |
| `GET` | `/api/history/` | **(Nouveau)** Liste des discussions de l'utilisateur |

**Exemple :**

```bash
curl -X POST http://127.0.0.1:8001/api/chatbot/ask/ \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Quels sont les frais d'inscription ?\", \"top_k\": 3}"
```

### Gen3 — `/api/v2/` (si monté)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v2/chatbot/status/` | État LLM / pipeline |
| `POST` | `/api/v2/chatbot/ask/` | RAG (JSON ou SSE `stream: true`) |
| `GET` | `/api/v2/chatbot/reload-index/` | Recharge index FAISS à chaud |

**Exemple streaming :**

```bash
curl -N -X POST http://127.0.0.1:8001/api/v2/chatbot/ask/ \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{\"question\": \"Où se trouve SUP'PTIC ?\", \"stream\": true}"
```

Documentation technique : `docs/backend/API_REST_IMPLEMENTATION.md`, `backend/chatbot/engine/README.md`.

---

## 10. Déploiement backend (Railway)

> **Procédure complète** (variables, bootstrap données, checklist) : **[DEPLOIEMENT.md](DEPLOIEMENT.md)**

### 10.1 Principe

Fichiers de déploiement à la racine :

| Fichier | Rôle |
|---------|------|
| `railway.json` | Healthcheck `/api/health/`, commande de démarrage |
| `nixpacks.toml` | Python 3.13, `pip install -r requirements.txt` |
| `backend/scripts/start_production.py` | migrate → collectstatic → Gunicorn |
| `deploy/railway.env.example` | Modèle de variables Railway |

Au démarrage : migrations, fichiers statiques, puis **Gunicorn** (timeout 120 s pour le pipeline ML).

### 10.2 Étapes Railway

1. Créer un projet Railway, connecter le dépôt Git.
2. Ajouter un service **PostgreSQL** (plugin Railway).
3. Lier `DATABASE_URL` au service Django (variable injectée automatiquement).
4. Définir les variables d’environnement (section 5.1, `DEBUG=False`).
5. Déployer ; noter l’URL publique (`https://xxx.up.railway.app`).

### 10.3 Post-déploiement (données & index)

Exécuter via **Railway Shell** ou en local avec `DATABASE_URL` de prod :

```bash
cd backend
python manage.py setup_demo
python manage.py setup_gen3 --allow-download   # si Gen3 souhaité
python manage.py check_gen3
```

> **Important** : sur un nouveau déploiement, la base Postgres est vide tant que `setup_demo` n’a pas été lancé. Sans FAQ ni vecteurs, le frontend affichera « hors ligne » ou des réponses vides.

### 10.4 Vérification

```bash
curl https://VOTRE-SERVICE.up.railway.app/api/health/
```

### 10.5 Autres hébergeurs (VPS, Render, etc.)

Équivalent :

```bash
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi --bind 0.0.0.0:8000
```

Utiliser un reverse proxy (Nginx) + HTTPS en production. Variables identiques à Railway.

---

## 11. Déploiement frontend (PWA / site statique)

### 11.1 Build

```powershell
cd frontend\app
# Définir l’URL du backend déployé
echo VITE_API_URL=https://VOTRE-SERVICE.up.railway.app > .env
npm run build
```

Sortie : **`frontend/app/dist/`** (fichiers statiques + service worker PWA).

### 11.2 Netlify

Le fichier `frontend/app/netlify.toml` configure build, redirections SPA et cache PWA.

1. Site → **Import** du dépôt GitHub.
2. **Base directory** : `frontend/app` (build/publish lus depuis `netlify.toml`).
3. Variable Netlify : `VITE_API_URL=https://...railway.app` (voir `deploy/netlify.env.example`).
4. Ajouter l'URL Netlify dans `CORS_ALLOWED_ORIGINS` du backend.
### 11.3 Vercel

Même principe : root `frontend/app`, framework Vite, variable `VITE_API_URL`, output `dist`.

### 11.4 Hébergement statique simple

```powershell
npx serve frontend\app\dist -l 3000
```

Configurer `VITE_API_URL` **avant** `npm run build` (les variables Vite sont figées au build).

### 11.5 CORS — rappel

En production (`DEBUG=False`), seules les origines listées dans `CORS_ALLOWED_ORIGINS` peuvent appeler l’API. Les regex `.up.railway.app` et `.netlify.app` couvrent déjà beaucoup de cas ; ajoutez votre domaine custom si besoin.

---

## 12. APK Android (Capacitor)

> **Documentation détaillée mobile** : [MOBILE.md](MOBILE.md) (UI native, clavier, scénarios réseau, checklist distribution).

### 12.1 Prérequis

- Node.js + `npm install` dans `frontend/app`
- **JDK 21** (Java 8/17 seuls échouent sur Capacitor 7)
- Android SDK (`ANDROID_HOME` ou `%LOCALAPPDATA%\Android\Sdk`)

Sous Windows, exemple :

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
```

### 12.2 Configurer l’API pour l’APK

Éditer `frontend/app/.env` **avant** le build :

```env
VITE_API_URL=https://VOTRE-SERVICE.up.railway.app
```

### 12.3 Construire l’APK debug

```powershell
cd frontend\app
npm run android:build
```

Ou avec détection JDK automatique :

```powershell
npm run android:build:win
```

**APK généré :**

```
frontend/app/android/app/build/outputs/apk/debug/app-debug.apk
```

### 12.4 Installer sur un appareil

```powershell
adb install frontend\app\android\app\build\outputs\apk\debug\app-debug.apk
```

Ou transférer le fichier `.apk` sur le téléphone (autoriser les sources inconnues).

### 12.5 APK release (Play Store)

1. Générer un keystore Android.
2. Configurer la signature dans `android/app/build.gradle`.
3. `cd android && .\gradlew.bat assembleRelease`
4. Signer / publier via Google Play Console.

### 12.6 Ouvrir le projet dans Android Studio

```powershell
npm run android:open
```

---

## 13. Dépannage

### Backend ne démarre pas en production

| Erreur | Solution |
|--------|----------|
| `SECRET_KEY doit être définie` | Définir `SECRET_KEY` dans les variables d’environnement |
| Erreur Postgres | Vérifier `DATABASE_URL` |
| Routes Gen3 absentes | `pip install sentence-transformers faiss-cpu google-generativeai` puis `setup_gen3` |

### Frontend « Serveur inaccessible »

| Cause | Solution |
|-------|----------|
| Backend arrêté | `python manage.py runserver 127.0.0.1:8001` |
| Mauvaise `VITE_API_URL` | Rebuild après correction du `.env` |
| CORS | Ajouter l’origine frontend dans `CORS_ALLOWED_ORIGINS` |
| APK + backend local | Utiliser l’IP LAN du PC, pas `localhost` |

### `phase1: indexing_required`

```powershell
cd backend
python manage.py rebuild_vectors
# ou
python manage.py setup_demo
```

### Gen3 indisponible

```powershell
python manage.py check_gen3
python manage.py setup_gen3 --allow-download
```

Vérifier `GEMINI_API_KEY` pour le niveau LLM.

### Build APK échoue (Java)

| Message | Action |
|---------|--------|
| `requires at least JVM runtime version 11` | Installer JDK 21, définir `JAVA_HOME` |
| `invalid source release: 21` | Utiliser JDK 21, pas JDK 17 |
| `Unsupported class file major version 68` | Ne pas utiliser JDK 24 pour Gradle ; utiliser JDK 21 |

### Gradle / SDK Android

```powershell
# Accepter les licences si demandé
sdkmanager --licenses
```

Installer **Android SDK Platform 35** via Android Studio → SDK Manager.

---

## 14. Checklist production

### Backend

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` unique et secrète
- [ ] `DATABASE_URL` Postgres configurée
- [ ] `ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS` renseignés
- [ ] `python manage.py migrate` exécuté
- [ ] `setup_demo` (ou données réelles + `rebuild_vectors`)
- [ ] (Optionnel) `setup_gen3` + `GEMINI_API_KEY`
- [ ] `GET /api/health/` → `status: ok`, `phase1: ready`

### Frontend / APK

- [ ] `VITE_API_URL` pointe vers le backend HTTPS
- [ ] `npm run build` sans erreur
- [ ] Test navigateur : chat, suggestions, streaming Gen3
- [ ] CORS : origine frontend autorisée

### Sécurité

- [ ] Fichier `.env` **non** commité (vérifier `.gitignore`)
- [ ] Clés API uniquement en variables d’environnement hébergeur
- [ ] HTTPS actif (Railway / Netlify le fournissent)

---

## Documentation complémentaire

| Document | Contenu |
|----------|---------|
| [README.md](../README.md) | Présentation projet |
| [DEPLOIEMENT.md](DEPLOIEMENT.md) | **Production** — Railway, Netlify, Vercel, CI |
| [MOBILE.md](MOBILE.md) | **APK Android** — build, réseau, UI, dépannage |
| [backend/README.md](../backend/README.md) | Commandes backend rapides |
| [frontend/app/README.md](../frontend/app/README.md) | React, PWA, APK |
| [docs/backend/ARCHITECTURE.md](backend/ARCHITECTURE.md) | Architecture détaillée |
| [docs/backend/API_TEST_GUIDE.md](backend/API_TEST_GUIDE.md) | Tests API |
| [backend/chatbot/engine/README.md](../backend/chatbot/engine/README.md) | Pipeline RAG Gen3 |

---

*Développé par le Club Informatique SUP'PTIC — SUP'ONE AI.*
