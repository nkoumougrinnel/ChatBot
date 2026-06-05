# Docker — SUP'ONE AI (serveur)

Déploiement **self-hosted** avec Docker Compose : PostgreSQL + API Django + frontend React (Nginx).

| Service | Image | Rôle |
|---------|-------|------|
| `db` | `postgres:16-alpine` | Base de données |
| `api` | build `docker/Dockerfile.backend` | Django + Gunicorn + Gen3 |
| `web` | build `docker/Dockerfile.frontend` | Nginx : PWA + proxy `/api` → `api` |

```
Navigateur
    │
    ▼ :80
┌─────────┐  /api/*   ┌─────────┐      ┌──────────┐
│   web   │ ────────► │   api   │ ───► │    db    │
│ (Nginx) │           │(Gunicorn)│      │(Postgres)│
└─────────┘           └─────────┘      └──────────┘
```

> Cloud managé (Railway / Netlify) : [DEPLOIEMENT.md](DEPLOIEMENT.md)

---

## 1. Prérequis serveur

| Outil | Version |
|-------|---------|
| Docker | 24+ |
| Docker Compose | v2 (`docker compose`) |
| RAM | **4 Go minimum** (8 Go recommandé — index ML) |
| Disque | **10 Go+** libres |

---

## 2. Installation rapide

```bash
git clone <url-du-depot> ChatBot
cd ChatBot

cp deploy/docker.env.example .env
# Éditer .env : POSTGRES_PASSWORD, SECRET_KEY, GEMINI_API_KEY, ALLOWED_HOSTS

docker compose up -d --build
```

Attendre que les healthchecks passent (~2–5 min au premier build).

### Initialiser les données (obligatoire)

```bash
# Linux / macOS
chmod +x scripts/docker-bootstrap.sh
./scripts/docker-bootstrap.sh
```

```powershell
# Windows
.\scripts\docker-bootstrap.ps1
```

Ou manuellement :

```bash
docker compose exec api python manage.py import_faq_json --allow-download
docker compose exec api python manage.py check_gen3
```

### Vérifier

- Interface : `http://IP_DU_SERVEUR/`
- API : `http://IP_DU_SERVEUR/api/health/`

---

## 3. Configuration (`.env`)

Modèle : [`deploy/docker.env.example`](../deploy/docker.env.example)

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Mot de passe Postgres (**obligatoire**) |
| `SECRET_KEY` | Clé Django (**obligatoire**) |
| `ALLOWED_HOSTS` | Domaine ou IP du serveur |
| `GEMINI_API_KEY` | Clé Gemini (niveau LLM Gen3) |
| `HTTP_PORT` | Port exposé (défaut `80`) |
| `VITE_API_URL` | Laisser **vide** (proxy Nginx `/api`) |
| `SECURE_SSL_REDIRECT` | `False` si HTTP seul ; `True` derrière HTTPS |
| `RUN_BOOTSTRAP` | `1` une fois pour jeu de démo auto (optionnel) |

Générer `SECRET_KEY` :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 4. Volumes persistants

| Volume | Contenu |
|--------|---------|
| `postgres_data` | Base PostgreSQL |
| `rag_data` | Index FAISS + cache TF-IDF Gen3 |
| `hf_cache` | Modèle MiniLM (HuggingFace) |

Les données survivent à `docker compose down`.  
`docker compose down -v` **supprime** les volumes.

---

## 5. Commandes utiles

```bash
# Logs
docker compose logs -f api
docker compose logs -f web

# Shell Django
docker compose exec api python manage.py shell

# Reconstruire après mise à jour du code
docker compose up -d --build

# Arrêter
docker compose down

# Santé
docker compose ps
curl http://localhost/api/health/
```

---

## 6. Importer le corpus FAQ complet

Par défaut, `backend/data/json/` contient un sous-ensemble. Pour le corpus validé :

```bash
# Copier les JSON validés dans le conteneur ou sur l'hôte avant rebuild
cp data/json/validated/*.json backend/data/json/
docker compose up -d --build api
docker compose exec api python manage.py import_faq_json --allow-download
```

---

## 7. HTTPS (production)

Docker expose le port **80** en HTTP. Pour HTTPS :

1. Placer un **reverse proxy** devant (Traefik, Caddy, Nginx + Certbot sur l'hôte).
2. Terminer TLS sur le proxy, rediriger vers `localhost:80`.
3. Dans `.env` :
   ```env
   SECURE_SSL_REDIRECT=True
   ALLOWED_HOSTS=localhost,votre-domaine.com
   ```

---

## 8. Fichiers Docker

| Fichier | Rôle |
|---------|------|
| `docker-compose.yml` | Orchestration 3 services |
| `docker/Dockerfile.backend` | Image Python 3.13 + ML |
| `docker/Dockerfile.frontend` | Build Vite + Nginx |
| `docker/nginx.conf` | SPA + proxy API + SSE |
| `docker/entrypoint.backend.sh` | Attente Postgres |
| `.dockerignore` | Exclusions build |

---

## 9. Dépannage

| Problème | Solution |
|----------|----------|
| `api` unhealthy au démarrage | `docker compose logs api` — migrations / Postgres |
| Build lent ou OOM | Augmenter RAM Docker ; `WEB_CONCURRENCY=1` |
| Frontend OK, API KO | `docker compose exec api curl localhost:8000/api/health/` |
| Gen3 indisponible | `import_faq_json --allow-download` ; vérifier `GEMINI_API_KEY` |
| `DisallowedHost` | Ajouter IP/domaine dans `ALLOWED_HOSTS` |
| Permission denied entrypoint | `git config core.autocrlf false` puis re-cloner, ou `dos2unix docker/entrypoint.backend.sh` |

---

## 10. Checklist serveur

- [ ] `.env` configuré (mots de passe, `SECRET_KEY`, `ALLOWED_HOSTS`)
- [ ] `docker compose up -d --build` réussi
- [ ] `import_faq_json --allow-download` exécuté
- [ ] `GET /api/health/` → `status: ok`
- [ ] Chat fonctionnel sur `http://IP/`
- [ ] Volumes sauvegardés (backup Postgres + `rag_data`)
- [ ] HTTPS configuré (production)

---

*Club Informatique SUP'PTIC — SUP'ONE AI.*
