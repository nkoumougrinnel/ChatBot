# Guide de Déploiement — SUP'ONE

**Backend** : Railway (branche `backend`) · Docker  
**Frontend** : Netlify · Expo React Native Web  
**Date** : Mai 2026

---

## Table des matières

1. [Structure du dépôt](#1-structure-du-dépôt)
2. [Prérequis](#2-prérequis)
3. [Déploiement Backend — Railway](#3-déploiement-backend--railway)
4. [Déploiement Frontend — Netlify](#4-déploiement-frontend--netlify)
5. [Connexion Frontend ↔ Backend](#5-connexion-frontend--backend)
6. [Dockerisation du backend](#6-dockerisation-du-backend)
7. [Vérification post-déploiement](#7-vérification-post-déploiement)
8. [Maintenance et mises à jour](#8-maintenance-et-mises-à-jour)

---

## 1. Structure du dépôt

Le dépôt contient deux parties dans deux branches séparées. Railway déploie uniquement la branche `backend`.

```
dépôt Git
├── branche: main
│   └── (développement général)
│
├── branche: backend          ← Railway pointe ici
│   └── backend/
│       ├── Dockerfile        ← Build Docker pour Railway
│       ├── railway.toml      ← Config Railway (à la racine du dépôt)
│       ├── Procfile
│       ├── runtime.txt
│       ├── requirements.txt
│       ├── manage.py
│       ├── config/
│       ├── chatbot/
│       ├── faq/
│       ├── users/
│       └── rag_data/         ← index.bin + metadata.json + tfidf_cache.pkl
│
└── branche: frontend (ou main)
    └── frontend/
        ├── netlify.toml      ← Config Netlify (à la racine du dépôt)
        └── react-app/
            ├── package.json
            ├── app/
            └── Service/
                └── api.ts    ← URL backend via EXPO_PUBLIC_BACKEND_URL
```

---

## 2. Prérequis

### Outils locaux

| Outil | Version | Installation |
|---|---|---|
| Git | >= 2.30 | `apt install git` |
| Node.js | >= 20 | [nodejs.org](https://nodejs.org) |
| npm | >= 9 | Inclus avec Node |
| Railway CLI | dernière | `npm install -g @railway/cli` |
| Netlify CLI | dernière | `npm install -g netlify-cli` |

### Comptes requis

- **Railway** : [railway.app](https://railway.app) — plan Developer recommandé (1 Go RAM, nécessaire pour MiniLM)
- **Netlify** : [netlify.com](https://netlify.com) — plan Free suffisant
- **Google AI Studio** : [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) — pour la clé Gemini

### Fichiers à placer dans le dépôt (branche `backend`)

Vérifier que ces fichiers sont commités et non ignorés :

```bash
# Depuis la branche backend
git ls-files backend/rag_data/
# Doit lister : index.bin, metadata.json, tfidf_cache.pkl

git ls-files backend/Dockerfile railway.toml
# Doit lister les deux fichiers
```

Si `rag_data/` est dans `.gitignore`, le corriger :

```bash
# backend/.gitignore — supprimer ou commenter la ligne :
# rag_data/

# Puis ajouter les fichiers
git add backend/rag_data/index.bin backend/rag_data/metadata.json backend/rag_data/tfidf_cache.pkl
git commit -m "feat: add rag_data for Railway deployment"
git push origin backend
```

---

## 3. Déploiement Backend — Railway

### Option A — Script automatique (recommandé)

```bash
# Depuis la racine du dépôt, sur la branche backend
git checkout backend

# Étape 1 — Première configuration
bash deploy_backend.sh --setup

# Étape 2 — Déploiement
bash deploy_backend.sh --deploy

# Étape 3 — Vérification
bash deploy_backend.sh --check
```

### Option B — Étapes manuelles

#### Étape 3.1 — Connexion Railway

```bash
railway login
# Ouvre le navigateur pour l'authentification
```

#### Étape 3.2 — Créer le projet Railway

```bash
# Sur la branche backend
git checkout backend

railway init
# Choisir : "Create new project"
# Nom : supone-backend (ou votre choix)
```

Ou via le dashboard : **railway.app → New Project → Deploy from GitHub repo** → sélectionner le dépôt → **branche `backend`**.

#### Étape 3.3 — Configurer le build Docker

Railway détecte automatiquement le `Dockerfile` grâce au `railway.toml` :

```toml
# railway.toml (à la racine de la branche backend)
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"
buildContext = "backend"
```

> **Pourquoi Docker et pas Nixpacks ?** Le backend charge MiniLM (`all-MiniLM-L6-v2`) et FAISS. Nixpacks peut avoir des problèmes avec `faiss-cpu` et `sentence-transformers` sur certaines versions. Le Dockerfile garantit un environnement reproductible.

#### Étape 3.4 — Ajouter PostgreSQL

Dans le dashboard Railway :
1. **New Service → Database → PostgreSQL**
2. Railway injecte automatiquement la variable `DATABASE_URL`

Activer PostgreSQL dans `backend/config/settings.py` — décommenter la ligne :

```python
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),  # ← décommenter cette ligne
        # default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",  # ← commenter celle-ci
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

Commiter ce changement sur la branche `backend` :

```bash
git add backend/config/settings.py
git commit -m "config: switch to PostgreSQL for production"
git push origin backend
```

#### Étape 3.5 — Variables d'environnement Railway

Dans le dashboard Railway → **Variables**, ou via CLI :

```bash
# Générer une SECRET_KEY sécurisée
SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

railway variables set \
    SECRET_KEY="$SECRET" \
    DEBUG="False" \
    DJANGO_SETTINGS_MODULE="config.settings" \
    TRANSFORMERS_OFFLINE="1" \
    HF_DATASETS_OFFLINE="1" \
    SCORE_DIRECT="0.55" \
    SCORE_LLM="0.30" \
    GEMINI_API_KEY="votre-cle-gemini" \
    GEMINI_MODEL="gemini-1.5-flash"
```

> **Remarque** : `ALLOWED_HOSTS` sera mis à jour après le premier déploiement, une fois que vous connaissez l'URL Railway générée.

#### Étape 3.6 — Lancer le déploiement

```bash
# Depuis la racine du dépôt, branche backend
railway up --detach

# Suivre les logs
railway logs --tail
```

Lignes attendues dans les logs :

```
Building Docker image...
[embedder] Chargement de all-MiniLM-L6-v2...
[embedder] Modèle chargé en X.Xs — dim=384
[embedder] Warm-up terminé.
[faiss_search] Chargé : 1050 vecteurs | 1050 métadonnées
[tfidf_fallback] TF-IDF chargé depuis cache
```

#### Étape 3.7 — Migrations et fixtures

```bash
# Exécuter les migrations dans l'environnement Railway
railway run python manage.py migrate

# Charger les données FAQ initiales
railway run python manage.py loaddata faq/fixtures/categories.json
railway run python manage.py loaddata faq/fixtures/faq.json
railway run python manage.py loaddata users/fixtures/users.json
```

#### Étape 3.8 — Récupérer l'URL et mettre à jour ALLOWED_HOSTS

```bash
# Afficher l'URL du service
railway domain
# Ex : supone-backend.up.railway.app
```

Mettre à jour `ALLOWED_HOSTS` :

```bash
railway variables set ALLOWED_HOSTS="localhost,127.0.0.1,supone-backend.up.railway.app,votre-site.netlify.app"
```

Puis mettre à jour `settings.py` pour lire depuis l'environnement :

```python
# backend/config/settings.py
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://localhost:3000",
    os.environ.get('NETLIFY_URL', 'https://your-site.netlify.app'),
]
```

Commiter et redéployer :

```bash
git add backend/config/settings.py
git commit -m "config: dynamic ALLOWED_HOSTS from env"
git push origin backend
railway up --detach
```

---

## 4. Déploiement Frontend — Netlify

### Préparation — Modifier api.ts

Remplacer l'IP hardcodée dans `frontend/react-app/Service/api.ts` par la variable d'environnement Expo :

```typescript
// Avant (à supprimer)
export const BACKEND_BASE_URL = "http://10.227.132.171:8000";

// Après (utiliser le fichier api.ts fourni)
export const BACKEND_BASE_URL =
  process.env.EXPO_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
```

Commiter ce changement.

### Option A — Script automatique

```bash
# Depuis la racine du dépôt

# Étape 1 — Installer les dépendances et configurer .env.local
bash deploy_frontend.sh --setup
# → Saisir l'URL Railway quand demandé

# Étape 2 — Preview (tester avant production)
bash deploy_frontend.sh --preview

# Étape 3 — Production
bash deploy_frontend.sh --deploy
```

### Option B — Déploiement via dashboard Netlify (sans CLI)

C'est la méthode la plus simple et la recommandée pour la première fois.

#### Étape 4.1 — Connecter le dépôt GitHub

1. Aller sur [app.netlify.com](https://app.netlify.com)
2. **Add new site → Import an existing project**
3. Sélectionner votre dépôt GitHub
4. Choisir la branche qui contient le frontend (ex : `main` ou `frontend`)

#### Étape 4.2 — Configurer le build

Netlify lit automatiquement `netlify.toml`. Vérifier que ces valeurs apparaissent dans l'interface :

| Champ | Valeur |
|---|---|
| Base directory | `frontend/react-app` |
| Build command | `npx expo export --platform web` |
| Publish directory | `frontend/react-app/dist` |

#### Étape 4.3 — Variables d'environnement Netlify

Dans **Site settings → Environment variables** :

| Variable | Valeur |
|---|---|
| `EXPO_PUBLIC_BACKEND_URL` | `https://supone-backend.up.railway.app` |
| `NODE_VERSION` | `20` |

#### Étape 4.4 — Lancer le build

Cliquer **Deploy site**. Netlify exécute :

```bash
cd frontend/react-app
npm install
npx expo export --platform web
# → génère frontend/react-app/dist/
```

#### Étape 4.5 — Configurer le domaine

Dans **Domain settings** :
- Netlify génère une URL du type `random-name.netlify.app`
- Vous pouvez la personnaliser : `supone.netlify.app`
- Ou connecter un domaine personnalisé si vous en avez un

---

## 5. Connexion Frontend ↔ Backend

### Schéma de communication

```
Utilisateur (mobile/web)
        │
        ▼
   Netlify CDN
   supone.netlify.app
        │  HTTPS + SSE
        ▼
   Railway Backend
   supone-backend.up.railway.app
        │
        ├── FAISS + MiniLM (en mémoire)
        ├── TF-IDF (en mémoire)
        ├── Gemini API (niveau LLM)
        └── PostgreSQL (Railway DB)
```

### Points de configuration à synchroniser

Après les deux déploiements, vérifier que ces valeurs correspondent :

**Côté backend (Railway variables) :**
```bash
ALLOWED_HOSTS=supone-backend.up.railway.app,supone.netlify.app
```

**Côté backend (settings.py) :**
```python
CORS_ALLOWED_ORIGINS = [
    "https://supone.netlify.app",
    "https://*.netlify.app",
]
CSRF_TRUSTED_ORIGINS = [
    "https://*.netlify.app",
    "https://*.up.railway.app",
]
```

**Côté frontend (Netlify variable) :**
```
EXPO_PUBLIC_BACKEND_URL=https://supone-backend.up.railway.app
```

### Test de la connexion

Depuis un navigateur, ouvrir la console et tester :

```javascript
fetch('https://supone-backend.up.railway.app/api/chatbot/ask/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: 'Bonjour', stream: false })
}).then(r => r.json()).then(console.log)
```

Résultat attendu :
```json
{ "answer": "Bonjour ! Je suis SUP'ONE...", "level": "conv", "method": "CONV" }
```

---

## 6. Dockerisation du backend

### Pourquoi Docker

- **Reproductibilité** : même environnement en dev, CI, et Railway
- **Contrôle des dépendances** : `faiss-cpu`, `sentence-transformers`, et `spacy` ont parfois des conflits avec Nixpacks
- **Build multi-étapes** : réduit la taille de l'image finale (~500 Mo vs ~1.2 Go sans multi-stage)

### Structure du Dockerfile (multi-stage)

```
Stage 1 — builder
    python:3.11-slim
    + build-essential, libpq-dev
    pip wheel → /wheels/*.whl
        │
        ▼
Stage 2 — image finale
    python:3.11-slim
    + libpq5, libgomp1 (runtime FAISS)
    + wheels copiés depuis builder
    + code source copié
    CMD gunicorn ...
```

### Build local (test avant push)

```bash
cd backend/

# Build de l'image
docker build -t supone-backend:local .

# Test local avec les variables d'environnement
docker run --rm \
    -p 8000:8000 \
    -e SECRET_KEY=test-key-local \
    -e DEBUG=True \
    -e GEMINI_API_KEY=votre-cle \
    -e TRANSFORMERS_OFFLINE=1 \
    -e HF_DATASETS_OFFLINE=1 \
    supone-backend:local

# Tester dans un autre terminal
curl http://localhost:8000/api/chatbot/status/
```

### Réduction de la taille d'image

L'image finale est ~500 Mo. Pour la réduire davantage :

```dockerfile
# Ajouter dans le Dockerfile avant COPY . .
# Supprimer les modèles HuggingFace non utilisés
# (si le modèle est déjà dans rag_data/ sous forme d'index FAISS)
RUN find /root/.cache/huggingface -name "*.bin" -size +50M -delete 2>/dev/null || true
```

### Docker Compose (développement local)

Créer `docker-compose.yml` à la racine de la branche `backend` pour le développement local avec PostgreSQL :

```yaml
# docker-compose.yml — développement local uniquement
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: supone_dev
      POSTGRES_USER: supone
      POSTGRES_PASSWORD: supone_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: backend/
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      SECRET_KEY: dev-secret-key-not-for-production
      DEBUG: "True"
      DATABASE_URL: postgresql://supone:supone_dev_password@db:5432/supone_dev
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      TRANSFORMERS_OFFLINE: "1"
      HF_DATASETS_OFFLINE: "1"
    volumes:
      # Montage du code pour le rechargement à chaud en dev
      - ./backend:/app
    depends_on:
      - db
    command: >
      sh -c "python manage.py migrate &&
             python manage.py loaddata faq/fixtures/categories.json &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload"

volumes:
  postgres_data:
```

Utilisation :

```bash
# Démarrer
docker-compose up

# Arrêter
docker-compose down

# Reconstruire après modification du Dockerfile
docker-compose up --build
```

---

## 7. Vérification post-déploiement

### Checklist backend (Railway)

```bash
BACKEND=https://supone-backend.up.railway.app

# 1. Health check pipeline
curl -s $BACKEND/api/chatbot/status/ | python3 -m json.tool
# Attendu : faiss_loaded=true, tfidf_loaded=true, ready=true

# 2. Niveau CONV (< 1 ms)
curl -s -X POST $BACKEND/api/chatbot/ask/ \
    -H "Content-Type: application/json" \
    -d '{"question":"Bonjour !","stream":false}' | python3 -m json.tool
# Attendu : level=conv

# 3. Niveau DIRECT (~150 ms)
curl -s -X POST $BACKEND/api/chatbot/ask/ \
    -H "Content-Type: application/json" \
    -d '{"question":"Quels sont les frais de scolarité ?","stream":false}' | python3 -m json.tool
# Attendu : level=direct, score >= 0.55

# 4. Niveau LLM (Gemini — ~2-5 s)
curl -s -X POST $BACKEND/api/chatbot/ask/ \
    -H "Content-Type: application/json" \
    -d '{"question":"Quel est le salaire moyen dun ingénieur au Cameroun ?","stream":false}' | python3 -m json.tool
# Attendu : level=llm, method=LLM

# 5. API FAQ
curl -s $BACKEND/api/faq/ | python3 -m json.tool
```

### Checklist frontend (Netlify)

1. Ouvrir l'URL Netlify dans un navigateur
2. Vérifier que l'écran de connexion s'affiche
3. Se connecter et envoyer un message
4. Vérifier que la réponse arrive (badge de méthode affiché)
5. Tester en mode mobile (DevTools → responsive)

### Problèmes fréquents

| Symptôme | Cause probable | Solution |
|---|---|---|
| `DisallowedHost` Django | URL Railway absente de `ALLOWED_HOSTS` | Ajouter l'URL dans la variable Railway |
| `CORS error` navigateur | Origine Netlify non dans `CORS_ALLOWED_ORIGINS` | Mettre à jour `settings.py` |
| Build Docker échoue sur `faiss-cpu` | Version Python incompatible | Vérifier `python:3.11-slim` dans Dockerfile |
| Frontend affiche une page blanche | Route SPA mal configurée | Vérifier le `[[redirects]]` dans `netlify.toml` |
| LLM retourne OFFBASE | `GEMINI_API_KEY` manquante | Vérifier les variables Railway |
| MiniLM ne charge pas | Fichier absent sur Railway | Vérifier `TRANSFORMERS_OFFLINE=1` et le cache |

---

## 8. Maintenance et mises à jour

### Mettre à jour le backend

```bash
git checkout backend
# Faire les modifications
git add -A
git commit -m "feat: description du changement"
git push origin backend
# Railway déclenche automatiquement un redéploiement
```

### Mettre à jour le frontend

```bash
# Via Git (si Netlify est connecté au dépôt)
git add -A
git commit -m "feat: description du changement"
git push
# Netlify déclenche automatiquement le build

# Via CLI pour forcer
bash deploy_frontend.sh --deploy
```

### Reconstruire l'index FAISS après ajout de FAQ

```bash
# Reconstruire localement
cd backend/
python scripts/build_index.py --source sqlite

# Commiter les nouveaux fichiers d'index
git add rag_data/index.bin rag_data/metadata.json rag_data/tfidf_cache.pkl
git commit -m "data: rebuild FAISS index with new FAQ entries"
git push origin backend
# Railway redéploie avec le nouvel index

# OU recharger à chaud sans redéploiement (si Railway est déjà en ligne)
curl -X GET https://supone-backend.up.railway.app/api/chatbot/reload-index/
```

### Surveiller les coûts

- **Railway** : vérifier la consommation RAM dans le dashboard (MiniLM ≈ 250 Mo, prévoir 512 Mo minimum)
- **Gemini** : le tier gratuit offre 15 req/min et 1 million de tokens/jour — suffisant pour un usage interne

---

*Club Informatique SUP'PTIC — Guide de déploiement — Mai 2026*
