# Déploiement — SUP'ONE AI

Guide pas à pas pour mettre en production le chatbot SUP'PTIC.

| Composant | Plateforme | Fichiers de config |
|-----------|------------|-------------------|
| **Serveur dédié / VPS** | **Docker Compose** (recommandé on-premise) | `docker-compose.yml`, `deploy/docker.env.example` — **[DOCKER.md](DOCKER.md)** |
| **Backend API** (Django + Postgres) | [Railway](https://railway.app) | `railway.json`, `nixpacks.toml`, `deploy/railway.env.example` |
| **Frontend PWA** (React + Vite) | [Netlify](https://netlify.com) (recommandé) ou [Vercel](https://vercel.com) | `frontend/app/netlify.toml`, `frontend/app/vercel.json` |
| **APK Android** | Build local (Capacitor) | [MOBILE.md](MOBILE.md) |
| **CI** | GitHub Actions | `.github/workflows/ci.yml` |

---

## Architecture cible

```
Utilisateur (navigateur / APK)
        │
        ▼
┌───────────────────┐     HTTPS      ┌────────────────────┐
│  Netlify / Vercel │ ──────────────► │  Railway (Django)  │
│  frontend/app     │    /api/*       │  + PostgreSQL      │
│  (PWA statique)   │                 │  Gunicorn + Gen3   │
└───────────────────┘                 └────────────────────┘
```

---

## 1. Backend — Railway

### 1.1 Créer le projet

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Sélectionner ce dépôt
3. **Add plugin** → **PostgreSQL** (Railway injecte `DATABASE_URL` automatiquement)

### 1.2 Variables d'environnement

Copier le modèle [`deploy/railway.env.example`](../deploy/railway.env.example) dans Railway → **Variables** :

| Variable | Obligatoire | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Oui | Clé aléatoire longue |
| `DEBUG` | Oui | `False` |
| `ALLOWED_HOSTS` | Oui | `.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | Oui | `https://votre-site.netlify.app` |
| `DATABASE_URL` | Oui | (auto via Postgres) |
| `GEMINI_API_KEY` | Recommandé | Clé Google AI Studio |
| `HF_OFFLINE` | Recommandé | `1` |

Générer `SECRET_KEY` :

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 1.3 Premier déploiement

Railway utilise `nixpacks.toml` + `railway.json` :

- Build : `pip install -r requirements.txt`
- Démarrage : `backend/scripts/start_production.py` (migrate → collectstatic → Gunicorn)
- Healthcheck : `GET /api/health/`

### 1.4 Initialiser les données (obligatoire)

La base Postgres est vide au premier déploiement. **Railway Shell** ou terminal local avec `DATABASE_URL` de prod :

```bash
cd backend
python manage.py migrate
python manage.py import_faq_json
python manage.py rebuild_vectors
python manage.py setup_gen3 --allow-download
python manage.py check_gen3
```

**Alternative rapide (jeu de démo)** :

```bash
python manage.py setup_demo
python manage.py setup_gen3 --allow-download
```

**Bootstrap automatique** (optionnel, premier déploiement uniquement) :

```env
RUN_BOOTSTRAP=1
```

Puis retirer cette variable après succès (évite de relancer à chaque redémarrage).

### 1.5 Vérification

```bash
curl https://VOTRE-SERVICE.up.railway.app/api/health/
```

Réponse attendue : `"status": "ok"`, `"phase1": "ready"`.

---

## 2. Frontend — Netlify (recommandé)

### 2.1 Créer le site

1. [netlify.com](https://netlify.com) → **Add new site** → **Import an existing project**
2. Connecter GitHub
3. **Build settings** :
   - **Base directory** : `frontend/app`
   - **Build command** : `npm ci && npm run build` (déjà dans `netlify.toml`)
   - **Publish directory** : `dist`

### 2.2 Variable d'environnement

Netlify → **Site configuration** → **Environment variables** :

```env
VITE_API_URL=https://VOTRE-SERVICE.up.railway.app
```

Modèle : [`deploy/netlify.env.example`](../deploy/netlify.env.example)

> `VITE_API_URL` est **figée au build**. Après changement, relancer un déploiement.

### 2.3 CORS backend

Ajouter l’URL Netlify dans Railway :

```env
CORS_ALLOWED_ORIGINS=https://votre-site.netlify.app
```

Les sous-domaines `*.netlify.app` sont aussi couverts par regex dans `settings.py`.

### 2.4 Vérification

1. Ouvrir `https://votre-site.netlify.app`
2. Statut en-tête : « En ligne »
3. Poser une question test (ex. frais d’inscription)

---

## 3. Frontend — Vercel (alternative)

1. [vercel.com](https://vercel.com) → **Import Project**
2. **Root Directory** : `frontend/app`
3. Framework : **Vite** (détecté via `vercel.json`)
4. Variable : `VITE_API_URL=https://VOTRE-SERVICE.up.railway.app`
5. Ajouter l’URL Vercel dans `CORS_ALLOWED_ORIGINS` du backend

---

## 4. APK Android (production)

```powershell
cd frontend\app
# .env : VITE_API_URL=https://VOTRE-SERVICE.up.railway.app
npm run android:build
```

Détails : [MOBILE.md](MOBILE.md)

---

## 5. CI GitHub Actions

Le workflow `.github/workflows/ci.yml` exécute à chaque push / PR :

- **Backend** : `python manage.py test`
- **Frontend** : `npm ci` + `npm run build`

Aucun secret requis pour la CI de base.

---

## 6. Checklist production

### Backend (Railway)

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` unique
- [ ] PostgreSQL lié (`DATABASE_URL`)
- [ ] `CORS_ALLOWED_ORIGINS` = URL frontend exacte
- [ ] FAQ importées + vecteurs (`import_faq_json` ou `setup_demo`)
- [ ] Gen3 : `setup_gen3` + `GEMINI_API_KEY`
- [ ] `GET /api/health/` → OK

### Frontend (Netlify / Vercel)

- [ ] `VITE_API_URL` = URL Railway HTTPS
- [ ] Build Netlify réussi
- [ ] Chat, suggestions, streaming testés
- [ ] PWA installable (Chrome → Installer)

### Sécurité

- [ ] `.env` non commité
- [ ] Clés API uniquement dans les dashboards hébergeurs
- [ ] HTTPS actif (Railway + Netlify le fournissent)

---

## 7. Dépannage rapide

| Problème | Solution |
|----------|----------|
| Frontend « Hors ligne » | Backend down ou mauvaise `VITE_API_URL` → rebuild frontend |
| Erreur CORS | Ajouter origine Netlify dans `CORS_ALLOWED_ORIGINS` |
| `phase1: indexing_required` | `python manage.py rebuild_vectors` sur Railway Shell |
| Gen3 indisponible | `setup_gen3 --allow-download`, vérifier `GEMINI_API_KEY` |
| Build Railway lent | Normal (ML : scikit-learn, sentence-transformers) |
| Healthcheck Railway échoue | Attendre fin du build ; vérifier logs migrate/gunicorn |

---

## Fichiers de référence

| Fichier | Rôle |
|---------|------|
| `railway.json` | Commande de démarrage + healthcheck |
| `nixpacks.toml` | Python 3.13, install deps |
| `backend/scripts/start_production.py` | Migrate, static, bootstrap optionnel, Gunicorn |
| `frontend/app/netlify.toml` | Build Netlify, SPA, cache PWA |
| `frontend/app/vercel.json` | Config Vercel alternative |
| `deploy/railway.env.example` | Variables backend |
| `deploy/netlify.env.example` | Variable frontend |

---

*Club Informatique SUP'PTIC — SUP'ONE AI.*
