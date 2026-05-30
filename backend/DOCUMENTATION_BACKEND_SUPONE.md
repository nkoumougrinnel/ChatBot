# Documentation Backend — ChatBot SUP'ONE

**Projet** : ChatBot SUP'PTIC — Assistant intelligent du Club Informatique  
**Version** : Génération 3 — LLM réactivé (mai 2026)  
**Stack** : Django 4.2 · FAISS · MiniLM · TF-IDF · Ollama (Phi-3) · Gunicorn · Railway

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture du pipeline](#2-architecture-du-pipeline)
3. [Structure des fichiers](#3-structure-des-fichiers)
4. [Endpoints API](#4-endpoints-api)
5. [Changements apportés en Génération 3](#5-changements-apportés-en-génération-3)
6. [Déploiement sur Railway](#6-déploiement-sur-railway)
7. [Conseils d'optimisation pour un vrai serveur](#7-conseils-doptimisation-pour-un-vrai-serveur)
8. [Tests réalisés et tests restants](#8-tests-réalisés-et-tests-restants)
9. [Variables d'environnement](#9-variables-denvironnement)

---

## 1. Vue d'ensemble

SUP'ONE est le chatbot officiel de SUP'PTIC. Le backend Django expose une API REST consommée par une application React Mobile. Le moteur de réponse est un **pipeline RAG à 4 niveaux** fonctionnant entièrement en local, sans API cloud.

### Évolution des générations

| Génération | Moteur | LLM appelé | Latence typique |
|---|---|---|---|
| Gen 1 (Phase 1) | TF-IDF pur | Non | ~50 ms |
| Gen 2 (Phase 2) | FAISS + Ollama | Oui (score ≥ 0.55) | 15–30 s |
| **Gen 3 (actuelle)** | **FAISS + TF-IDF + Ollama** | **Oui (score < 0.30 uniquement)** | **< 300 ms ou 15–30 s** |

Le principe de la Gen 3 : le LLM est réservé aux questions hors base (score FAISS < 0.30), et reçoit toujours les top-3 résultats FAISS comme contexte même si leurs scores sont faibles. Si Ollama est indisponible, le pipeline bascule proprement sur un refus OFFBASE.

---

## 2. Architecture du pipeline

### Pipeline à 4 niveaux

```
Question utilisateur
        │
        ▼
┌─────────────────────────┐
│  Niveau 1 — CONV        │  Regex sur formules de politesse          < 1 ms
│  "Bonjour", "Merci"…    │  → Réponse hardcodée immédiate
└─────────────────────────┘
        │ (pas de match regex)
        ▼
   Vectorisation MiniLM (all-MiniLM-L6-v2, 384 dim)
   + Cache LRU (lru_cache maxsize=256)
        │
        ▼
   FAISS IndexFlatIP — top-3 voisins + score cosinus
        │
        ├─── score ≥ 0.55 ──────────────────────────────────────────────────┐
        │                                                                    ▼
        │                                                       Niveau 2 — DIRECT
        │                                                       Réponse FAISS brute    ~150 ms
        │
        ├─── 0.30 ≤ score < 0.55 ───────────────────────────────────────────┐
        │                                                                    ▼
        │                                                       Niveau 3 — TF-IDF
        │                                                       Fallback Phase 1       ~50 ms
        │
        └─── score < 0.30 ──────────────────────────────────────────────────┐
                                                                             ▼
                                                               Niveau 4 — LLM
                                                               top-3 FAISS → prompt Phi-3
                                                               Ollama génère la réponse  ~15-30 s
                                                                             │
                                                               Ollama indisponible ?
                                                                    │
                                                                    ▼
                                                               OFFBASE (refus propre)   < 1 ms
```

### Comportement du niveau LLM

Quand le score FAISS est < 0.30, les top-3 résultats sont quand même récupérés et injectés dans le prompt Phi-3 via `build_prompt()` :

```
[CONTEXTE]
[1] Admissions | e-supptic.cm
    <reponse_enrichie du résultat 1>

[2] Frais | brochure_2025.pdf
    <reponse_enrichie du résultat 2>

[3] Général
    <reponse_enrichie du résultat 3>

Question : <question de l'étudiant>
Réponds uniquement à partir du [CONTEXTE], en français, de façon concise.
```

Phi-3 s'appuie sur ce contexte faible pour tenter une réponse. Si l'information n'est vraiment pas dans le contexte, le message système (`_SYSTEM_MESSAGE`) lui impose de répondre : _"Je n'ai pas cette information dans ma base. Contactez le secrétariat."_

### Composants du moteur (`chatbot/engine/`)

| Fichier | Rôle |
|---|---|
| `embedder.py` | Singleton MiniLM thread-safe, warm-up auto, `encode()` / `encode_batch()` |
| `faiss_search.py` | Index FAISS `IndexFlatIP`, chargement via `AppConfig.ready()`, reload à chaud |
| `tfidf_fallback.py` | TF-IDF scikit-learn encapsulé comme fallback, cache pickle thread-safe |
| `prompt_builder.py` | Détection CONV par regex, `build_prompt()` avec injection top-3 contextes |
| `rag_pipeline.py` | **Orchestrateur principal** — `ask()` (JSON) et `ask_stream()` (SSE) |
| `llm_client.py` | Client HTTP Ollama, circuit-breaker, retry exponentiel — appelé au niveau 4 |

### Protocole SSE (streaming)

`ask_stream()` émet des événements W3C `text/event-stream`. `views.py` les retransmet au frontend en JSON typé :

| Événement SSE brut | JSON retransmis au frontend |
|---|---|
| `event: start` / `data: llm\|llm_phi3` | `{"type":"status","status":"searching"}` puis `{"type":"status","status":"generating"}` puis `{"type":"meta","level":"llm","method":"LLM"}` |
| `event: start` / `data: direct\|faiss_direct` | `{"type":"status","status":"searching"}` puis `{"type":"meta","level":"direct","method":"DIRECT"}` |
| `data: <token>` | `{"type":"token","content":"<token>"}` |
| `event: done` / `data: 142.3` | `{"type":"done","elapsed_ms":142}` |
| `event: error` / `data: <msg>` | `{"type":"error","message":"<msg>"}` |

Le statut `"generating"` est émis uniquement pour le niveau LLM, permettant au frontend d'afficher un indicateur spécifique ("Phi-3 génère une réponse…") distinct du simple `"searching"`.

---

## 3. Structure des fichiers

```
backend/
├── chatbot/
│   ├── apps.py                  # AppConfig — charge FAISS + TF-IDF au démarrage
│   ├── views.py                 # 4 endpoints : ask, status, reload-index, test-llm
│   ├── urls.py                  # Routes /api/chatbot/*
│   ├── engine/
│   │   ├── embedder.py          # MiniLM vectorisation
│   │   ├── faiss_search.py      # FAISS + seuils SCORE_DIRECT / SCORE_LLM
│   │   ├── llm_client.py        # Client Ollama — appelé au niveau 4 (LLM)
│   │   ├── prompt_builder.py    # Regex CONV + build_prompt() avec contextes FAISS
│   │   ├── rag_pipeline.py      # Orchestrateur ask() / ask_stream() — 4 niveaux
│   │   └── tfidf_fallback.py    # TF-IDF scikit-learn fallback
│   └── tests/
│       ├── test_embedder.py     # 9 tests
│       ├── test_faiss_search.py # 11 tests
│       └── test_fallback.py     # 13 tests
├── faq/                         # App Phase 1 — CRUD FAQ, Feedback, Stats
├── config/
│   ├── settings.py              # Configuration Railway-ready + SQLite/Postgres
│   ├── urls.py                  # Router principal API
│   └── wsgi.py
├── scripts/
│   ├── build_index.py           # Génère index.bin + metadata.json
│   └── run_full_test_suite.py   # Suite de tests complète
├── rag_data/
│   ├── index.bin                # Index FAISS (~1.3 Mo)
│   ├── metadata.json            # Mapping vecteur_id → réponse/catégorie/source
│   └── tfidf_cache.pkl          # Cache TF-IDF (~476 Ko)
├── Procfile                     # web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
├── runtime.txt                  # python-3.13.12
└── requirements.txt
```

---

## 4. Endpoints API

### Chatbot

| Méthode | URL | Description |
|---|---|---|
| `POST` | `/api/chatbot/ask/` | Pipeline principal — réponse JSON ou SSE |
| `GET` | `/api/chatbot/status/` | Health check Ollama + état FAISS/TF-IDF |
| `GET` | `/api/chatbot/reload-index/` | Recharge FAISS à chaud sans redémarrer |
| `POST` | `/api/chatbot/test-llm/` | Mesure la latence brute du LLM (debug) |

### FAQ (Phase 1, inchangée)

| Méthode | URL | Description |
|---|---|---|
| `GET/POST` | `/api/categories/` | CRUD catégories |
| `GET/POST` | `/api/faq/` | CRUD questions/réponses |
| `GET/POST` | `/api/feedback/` | Likes/dislikes |
| `GET` | `/api/stats/` | Statistiques globales |
| `GET` | `/api/stats/categories/` | Stats par catégorie |

### Exemple d'appel — mode JSON

```bash
# Réponse DIRECT (score ≥ 0.55)
curl -X POST https://<domaine>/api/chatbot/ask/ \
     -H "Content-Type: application/json" \
     -d '{"question": "Quels sont les frais de scolarité ?", "stream": false}'

# Réponse attendue
{
  "answer": "Les frais de scolarité à SUP'PTIC s'élèvent à...",
  "method": "DIRECT",
  "level": "direct",
  "score": 0.8712,
  "latency_ms": 148.3,
  "source": "e-supptic.cm",
  "categorie": "Admissions"
}

# Réponse LLM (score < 0.30, Ollama disponible)
curl -X POST https://<domaine>/api/chatbot/ask/ \
     -H "Content-Type: application/json" \
     -d '{"question": "Quel est le débouché d'\''un ingénieur en télécoms ?", "stream": false}'

# Réponse attendue
{
  "answer": "Un ingénieur en télécommunications peut exercer dans...",
  "method": "LLM",
  "level": "llm",
  "score": 0.2143,
  "latency_ms": 18420.0,
  "source": "ollama",
  "categorie": ""
}
```

---

## 5. Changements apportés en Génération 3

### Changement principal : réorganisation des niveaux et réactivation LLM ciblée

La Gen 2 appelait Ollama pour **toutes** les questions avec score FAISS ≥ 0.55, ce qui causait 15–30 s de latence sur la majorité des questions. La Gen 3 inverse la logique :

- Les questions bien couvertes par la base (score ≥ 0.55) → réponse instantanée FAISS directe
- Les questions partiellement couvertes (0.30 ≤ score < 0.55) → TF-IDF rapide
- Les questions hors base (score < 0.30) → LLM avec contexte FAISS, car c'est là que la génération apporte de la valeur

### `rag_pipeline.py` — refonte complète des niveaux

**Niveau 3 (TF-IDF)** : la condition passe de `score < 0.55` à `0.30 ≤ score < 0.55`. TF-IDF n'est plus un fallback en cas d'échec LLM, c'est un niveau à part entière plus rapide que le LLM pour les questions partiellement connues.

**Niveau 4 (LLM)** — nouveau : déclenché quand `score < SCORE_LLM` (0.30). Le pipeline :
1. Appelle `check_availability()` pour vérifier qu'Ollama est joignable
2. Si indisponible → bascule immédiate sur le refus OFFBASE (pas d'attente de timeout)
3. Si disponible → appelle `build_prompt(question, contexts, history)` avec les top-3 résultats FAISS
4. Appelle `generate_stream()` en streaming token par token
5. En cas d'exception pendant la génération → bascule sur OFFBASE

Les top-3 contextes sont **toujours passés** même avec des scores faibles (ex. 0.15, 0.12, 0.08). Phi-3 peut s'en servir comme point de départ même si la correspondance est imparfaite.

**Suppression du niveau OFFBASE comme niveau fixe** : OFFBASE n'est plus un niveau de pipeline à part entière, c'est le fallback du niveau LLM quand Ollama est indisponible.

### `views.py` — ajout du statut `generating`

Quand `ask_stream()` émet `event: start` avec `level=llm`, `views.py` émet maintenant trois événements consécutifs vers le frontend :

```
{"type": "status", "status": "searching"}    ← FAISS consulté
{"type": "status", "status": "generating"}   ← LLM en cours  ← NOUVEAU
{"type": "meta",   "level": "llm", "method": "LLM", "score": 0.0}
```

Le frontend peut utiliser `"generating"` pour afficher un message spécifique ("Phi-3 réfléchit…") et préparer l'utilisateur à une latence plus longue.

### `llm_client.py` — corrections de robustesse

- **Timeout** : `READ_TIMEOUT` corrigé à 180 s (configurable via `OLLAMA_READ_TIMEOUT`). L'ancienne valeur hardcodée de 5 s causait systématiquement un timeout lors de la génération Phi-3 (~15–20 s sur CPU).
- **Circuit-breaker** : après 3 échecs consécutifs, les appels Ollama sont bloqués 30 s. Évite d'empiler des timeouts qui bloqueraient les workers Gunicorn.
- **Retry exponentiel** : 2 tentatives avec attente 0.5 s puis 1 s sur `ConnectionRefusedError` / `BrokenPipeError`.
- **Suppression du système de session** : `_session_prompt`, `init_session`, `is_initialized` retirés — inutiles avec le nouveau pipeline.

### `embedder.py` — warm-up automatique

Après le chargement du modèle MiniLM, un appel `_model.encode(["warm-up"])` est effectué pour éliminer la latence JIT de la première vraie requête (qui pouvait atteindre 2–3 s à froid).

### `prompt_builder.py` — correction bug variable morte

Suppression de la variable `user_turn` contenant `chr(10).join()` dans une f-string — provoquait une `SyntaxError` silencieuse en Gen 2. `build_prompt()` est maintenant utilisé en production au niveau 4.

### `faiss_search.py` — `confidence_level` et élargissement de recherche

- Ajout de `confidence_level` dans `search_with_metadata()` : `"direct"` / `"llm"` / `"offbase"` selon le score, pour que `rag_pipeline.py` n'ait pas à recalculer les seuils.
- Élargissement : recherche `k + 2` voisins puis filtre à `k`, pour compenser les vecteurs `-1` (padding FAISS sur petits index).
- Seuils `SCORE_DIRECT` et `SCORE_LLM` exportés et configurables via variables d'environnement.

### `tfidf_fallback.py` — corrections encodage

- Gestion du BOM UTF-8 (`utf-8-sig`) sur les fichiers JSON produits sous Windows.
- Correction encodage Latin-1 → UTF-8 (`Ã©` → `é`).
- Compatibilité format JSON v1 (`answer`) et v2 (`reponse_enrichie`).

### `build_index.py` — déduplication et sauvegarde atomique

- Déduplication cross-fichiers via un `set` global `seen_questions`.
- Sauvegarde atomique : `index.bin.tmp` puis rename — évite la corruption en cas d'interruption.
- Mode `--source sqlite` pour construire l'index depuis la base Django directement.

---

## 6. Déploiement sur Railway

### Contrainte importante — Ollama sur Railway

Railway ne supporte pas Ollama en natif (pas de binaire compatible dans l'environnement Nixpacks, pas de GPU). Pour le niveau 4 (LLM), Ollama doit tourner **sur un serveur séparé** (VPS, machine locale exposée, instance dédiée) et être accessible via la variable `OLLAMA_BASE_URL`.

Si `OLLAMA_BASE_URL` pointe vers un serveur indisponible, le pipeline bascule automatiquement sur le refus OFFBASE — les niveaux 1, 2 et 3 continuent de fonctionner normalement. Le chatbot reste utilisable même sans Ollama.

### Étape 1 — Préparer le dépôt

Vérifier que ces fichiers sont présents à la racine de `backend/` :

```
Procfile    → web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
runtime.txt → python-3.13.12
requirements.txt
```

Commiter les fichiers `rag_data/` dans Git (nécessaires au démarrage) :

```bash
git add backend/rag_data/index.bin
git add backend/rag_data/metadata.json
git add backend/rag_data/tfidf_cache.pkl
git commit -m "feat: add rag_data files for deployment"
```

### Étape 2 — Créer le projet Railway

```bash
npm install -g @railway/cli
railway login
railway init        # depuis la racine du dépôt
```

Ou via le dashboard : **New Project → Deploy from GitHub repo**.

### Étape 3 — Ajouter PostgreSQL

Dans le dashboard : **New Service → Database → PostgreSQL**. Railway injecte automatiquement `DATABASE_URL`.

Dans `settings.py`, décommenter la ligne `DATABASE_URL` :

```python
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),   # Railway injecte cette variable
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

### Étape 4 — Variables d'environnement

```bash
railway variables set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
railway variables set DEBUG=False
railway variables set DJANGO_SETTINGS_MODULE=config.settings
railway variables set TRANSFORMERS_OFFLINE=1
railway variables set HF_DATASETS_OFFLINE=1
railway variables set SCORE_DIRECT=0.55
railway variables set SCORE_LLM=0.30

# Ollama sur serveur externe (facultatif — sans ça, niveau LLM → OFFBASE)
railway variables set OLLAMA_BASE_URL=https://votre-serveur-ollama.example.com
railway variables set OLLAMA_MODEL=phi3:mini
railway variables set OLLAMA_READ_TIMEOUT=180
```

### Étape 5 — ALLOWED_HOSTS

```python
# settings.py
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
```

```bash
railway variables set ALLOWED_HOSTS=votre-projet.up.railway.app,localhost
```

### Étape 6 — Build Command

Créer `railway.toml` à la racine du dépôt :

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120"
healthcheckPath = "/api/chatbot/status/"
healthcheckTimeout = 30
```

Le `--timeout 120` est indispensable : MiniLM met 5–15 s à charger selon le plan Railway, et Gunicorn tuerait le worker sans ce délai.

### Étape 7 — Déployer

```bash
railway up
# ou : git push origin main  (si la branche est liée)
railway logs    # surveiller le démarrage
```

Lignes attendues dans les logs :

```
[embedder] Chargement de all-MiniLM-L6-v2...
[embedder] Modèle chargé en X.Xs — dim=384
[embedder] Warm-up terminé.
[faiss_search] Chargé : 1050 vecteurs | 1050 métadonnées
[tfidf_fallback] TF-IDF chargé depuis cache
```

### Étape 8 — Vérifier

```bash
# Health check
curl https://votre-projet.up.railway.app/api/chatbot/status/

# Test niveau DIRECT
curl -X POST https://votre-projet.up.railway.app/api/chatbot/ask/ \
     -H "Content-Type: application/json" \
     -d '{"question": "Quels sont les frais de scolarité ?", "stream": false}'

# Test niveau LLM (si Ollama configuré)
curl -X POST https://votre-projet.up.railway.app/api/chatbot/ask/ \
     -H "Content-Type: application/json" \
     -d '{"question": "Quel temps fait-il à Yaoundé ?", "stream": false}'
```

### Points d'attention Railway

**Mémoire** : MiniLM consomme ~250 Mo. Le plan Starter (512 Mo) est juste — préférer le plan Developer (1 Go+).

**Éphémèreté du filesystem** : les fichiers `rag_data/` doivent être dans Git ou dans un volume Railway. Ne pas compter sur un `build_index.py` exécuté pendant le build.

**Latence LLM et timeouts HTTP** : si le frontend appelle via SSE avec un timeout court (< 30 s), il peut couper la connexion avant que Phi-3 ait fini de générer. Configurer un timeout SSE d'au moins 60 s côté frontend pour le niveau LLM.

---

## 7. Conseils d'optimisation pour un vrai serveur

### Configuration Gunicorn

```bash
gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --log-level info \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log
```

Utiliser `gthread` (threads) plutôt que `gevent` (greenlets) : les singletons FAISS et MiniLM utilisent des `threading.Lock()` qui conflictent avec les greenlets gevent. Avec gthread, les threads partagent les singletons sans recharger le modèle.

### Configuration Nginx pour le SSE

```nginx
# Route SSE — buffering désactivé obligatoirement
location /api/chatbot/ask/ {
    proxy_pass         http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header   Connection "";
    proxy_buffering    off;           # CRITIQUE — sans ça, les tokens LLM arrivent en bloc
    proxy_read_timeout 120s;          # LLM peut prendre 30 s
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
}

# Routes classiques
location /api/ {
    proxy_pass       http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_read_timeout 30s;
}
```

Le header `X-Accel-Buffering: no` est déjà émis par `views.py`, mais désactiver `proxy_buffering` dans Nginx sur la route `/api/chatbot/ask/` est nécessaire en complément pour que le streaming token-par-token soit visible en temps réel côté utilisateur.

### Ollama sur le même serveur

Si Ollama tourne en local sur le serveur :

```bash
# Démarrer Ollama comme service systemd
sudo systemctl enable ollama
sudo systemctl start ollama

# Vérifier
curl http://localhost:11434/api/tags
```

Configurer dans `.env` ou la variable d'environnement :
```
OLLAMA_BASE_URL=http://localhost:11434
```

Pour réduire la latence LLM sur CPU, tester ces paramètres dans `llm_client.py` :

```python
_PARAMS_LLM = {
    "temperature":  0.3,
    "num_predict":  256,      # Réduire de 512 à 256 pour des réponses plus courtes
    "top_p":        0.90,
    "num_ctx":      1024,     # Réduire le contexte si les réponses sont courtes
    "num_thread":   4,        # Nombre de threads CPU pour Ollama
}
```

### Cache sémantique — tuning

Le cache LRU dans `rag_pipeline.py` (`maxsize=256`) et dans `embedder.py` (`encode_cached`, `maxsize=512`) mémorisent les vecteurs des questions fréquentes. Avec plusieurs workers Gunicorn, chaque worker a son propre cache. Pour maximiser l'efficacité, pré-chauffer le cache au démarrage :

```python
# chatbot/apps.py — ajouter après le chargement FAISS/TF-IDF
def ready(self):
    from chatbot.engine import faiss_search, tfidf_fallback
    faiss_search.load_index()
    tfidf_fallback.load()

    # Pré-chauffe le cache avec les questions les plus fréquentes
    from chatbot.engine.rag_pipeline import _cached_encode
    TOP_QUESTIONS = [
        "Quels sont les frais de scolarité ?",
        "Comment s'inscrire à SUP'PTIC ?",
        "Quelles sont les filières disponibles ?",
        # ... compléter depuis les logs Feedback
    ]
    for q in TOP_QUESTIONS:
        _cached_encode(q)
```

### Base de données — passer à PostgreSQL

SQLite pose des verrous globaux en écriture. Dès 10 utilisateurs simultanés, les enregistrements de feedback commencent à bloquer. Migrer vers PostgreSQL :

```python
# settings.py — production
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME'),
        'USER':     os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS':  {'connect_timeout': 10},
    }
}
```

### Reconstruction périodique de l'index

Cron nightly pour reconstruire l'index si de nouvelles FAQ ont été ajoutées, puis recharger à chaud :

```bash
# /etc/cron.d/supone-index
0 2 * * * chatbot cd /var/www/supptic-chatbot && \
    python scripts/build_index.py --source sqlite && \
    curl -s http://localhost:8000/api/chatbot/reload-index/ >> /var/log/supone/index.log
```

---

## 8. Tests réalisés et tests restants

### Tests unitaires existants (33 tests)

```bash
cd backend
python manage.py test chatbot.tests
# Résultat attendu : Ran 33 tests — OK
```

#### `test_embedder.py` (9 tests)
Forme du vecteur (384 dim, float32), norme normalisée (≈ 1.0), similarité sémantique, texte vide → vecteur nul, latence < 500 ms, cache `encode_cached`.

#### `test_faiss_search.py` (11 tests)
Chargement (`is_loaded()`), cohérence vecteurs/métadonnées, pertinence sur 20 questions connues (score ≥ 0.50), robustesse hors domaine, reload à chaud.

#### `test_fallback.py` (13 tests)
Chargement cache TF-IDF, réponses domaine SUP'PTIC, bascule depuis `rag_pipeline.py` (score dans `[0.30, 0.55[`), hors domaine (score < 0.05), interface `search()`.

### Tests à réaliser

#### Tests d'intégration API — niveau LLM (priorité haute)

```python
# chatbot/tests/test_views.py

from unittest.mock import patch
from django.test import TestCase, Client
import json

class AskChatbotViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ask_json_direct(self):
        response = self.client.post(
            '/api/chatbot/ask/',
            data=json.dumps({"question": "Quels sont les frais de scolarité ?", "stream": False}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data['level'], ['direct', 'tfidf', 'conv'])

    def test_ask_empty_question(self):
        response = self.client.post(
            '/api/chatbot/ask/',
            data=json.dumps({"question": "", "stream": False}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_ask_llm_level_ollama_available(self):
        """Score < 0.30, Ollama disponible → level llm."""
        with patch('chatbot.engine.llm_client.check_availability') as mock_check, \
             patch('chatbot.engine.llm_client.generate') as mock_gen:
            mock_check.return_value = {"available": True, "model": "phi3:mini", "error": None}
            mock_gen.return_value = "Voici une réponse générée par Phi-3."
            response = self.client.post(
                '/api/chatbot/ask/',
                data=json.dumps({"question": "Quel est le prix du bitcoin ?", "stream": False}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['level'], 'llm')
        self.assertEqual(data['method'], 'LLM')

    def test_ask_offbase_when_ollama_unavailable(self):
        """Score < 0.30, Ollama indisponible → level offbase."""
        with patch('chatbot.engine.llm_client.check_availability') as mock_check:
            mock_check.return_value = {
                "available": False,
                "model": "phi3:mini",
                "error": "Ollama inaccessible"
            }
            response = self.client.post(
                '/api/chatbot/ask/',
                data=json.dumps({"question": "Quel est le prix du bitcoin ?", "stream": False}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['level'], 'offbase')

    def test_ask_streaming_llm_emits_generating_status(self):
        """Mode SSE niveau LLM — statut 'generating' doit être émis."""
        with patch('chatbot.engine.llm_client.check_availability') as mock_check, \
             patch('chatbot.engine.llm_client.generate_stream') as mock_stream:
            mock_check.return_value = {"available": True, "model": "phi3:mini", "error": None}
            mock_stream.return_value = iter(["Voici ", "une réponse."])
            response = self.client.post(
                '/api/chatbot/ask/',
                data=json.dumps({"question": "Quel est le prix du bitcoin ?", "stream": True}),
                content_type='application/json',
            )
        content = b"".join(response.streaming_content).decode()
        self.assertIn('"generating"', content)
        self.assertIn('"LLM"', content)

    def test_llm_status_returns_pipeline_health(self):
        response = self.client.get('/api/chatbot/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('pipeline', data)
        self.assertTrue(data['pipeline']['faiss_loaded'])
        self.assertTrue(data['pipeline']['tfidf_loaded'])
```

#### Tests de performance par niveau (priorité haute)

```python
# chatbot/tests/test_performance.py

import time
from unittest.mock import patch
from django.test import TestCase
from chatbot.engine.rag_pipeline import ask

class PerformanceTest(TestCase):

    def test_conv_latency_under_5ms(self):
        start = time.time()
        result = ask("Bonjour !")
        self.assertEqual(result.level, "conv")
        self.assertLess((time.time() - start) * 1000, 5)

    def test_direct_latency_under_300ms(self):
        start = time.time()
        result = ask("C'est combien pour s'inscrire à SUP'PTIC ?")
        self.assertIn(result.level, ["direct", "tfidf"])
        self.assertLess((time.time() - start) * 1000, 300)

    def test_llm_not_called_on_direct_level(self):
        """Le LLM ne doit pas être appelé quand score ≥ 0.55."""
        with patch('chatbot.engine.llm_client.generate') as mock_gen:
            ask("Quels sont les frais de scolarité ?")
            mock_gen.assert_not_called()

    def test_llm_called_on_offbase_question(self):
        """Le LLM doit être appelé quand score < 0.30 et Ollama disponible."""
        with patch('chatbot.engine.llm_client.check_availability') as mock_check, \
             patch('chatbot.engine.llm_client.generate') as mock_gen:
            mock_check.return_value = {"available": True, "model": "phi3:mini", "error": None}
            mock_gen.return_value = "Réponse LLM test."
            result = ask("Quel est le prix du bitcoin aujourd'hui ?")
            if result.level == "llm":   # seulement si le score est vraiment < 0.30
                mock_gen.assert_called_once()

    def test_cache_speedup(self):
        question = "Quels sont les frais de scolarité ?"
        t0 = time.time(); ask(question); t1 = time.time() - t0
        t0 = time.time(); ask(question); t2 = time.time() - t0
        self.assertLess(t2, t1 * 0.6)
```

#### Tests de charge (priorité moyenne)

```python
# locustfile.py — pip install locust
from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 3)

    @task(4)
    def ask_direct(self):
        self.client.post("/api/chatbot/ask/", json={
            "question": "Quels sont les frais de scolarité ?", "stream": False
        })

    @task(2)
    def ask_tfidf(self):
        self.client.post("/api/chatbot/ask/", json={
            "question": "tarif inscription supptic", "stream": False
        })

    @task(1)
    def ask_llm(self):
        # timeout long pour le niveau LLM
        self.client.post("/api/chatbot/ask/", json={
            "question": "Quel est le débouché d'un ingénieur télécoms ?", "stream": False
        }, timeout=60)

    @task(2)
    def ask_conv(self):
        self.client.post("/api/chatbot/ask/", json={
            "question": "Bonjour !", "stream": False
        })

# Lancer : locust -f locustfile.py --host=http://localhost:8000
# Objectif : 20 users, p95 < 500 ms (hors niveau LLM), zéro erreur 500
```

#### Tests de régression pipeline (priorité moyenne)

```python
# scripts/regression_test.py
CANONICAL_CASES = [
    ("Bonjour !",                                       "conv"),
    ("Merci beaucoup",                                  "conv"),
    ("Quels sont les frais de scolarité ?",             "direct"),
    ("Comment s'inscrire à SUP'PTIC ?",                 "direct"),
    ("Comment rejoindre le club informatique ?",         "direct"),
    ("tarif scol supptic",                              "tfidf"),
    ("inscription formation info",                      "tfidf"),
    # Pour les cas LLM, vérifier que le niveau est llm OU offbase
    # (dépend de la disponibilité d'Ollama dans l'environnement de test)
    ("Quel temps fait-il à Yaoundé ?",                  "llm_or_offbase"),
    ("Prix du bitcoin",                                 "llm_or_offbase"),
]
```

#### Test de fallback OFFBASE en cas d'erreur LLM (priorité haute)

```python
# chatbot/tests/test_llm_fallback.py

from unittest.mock import patch
from django.test import TestCase
from chatbot.engine.rag_pipeline import ask

class LLMFallbackTest(TestCase):

    def test_offbase_on_ollama_unavailable(self):
        with patch('chatbot.engine.llm_client.check_availability') as mock:
            mock.return_value = {"available": False, "model": "phi3:mini", "error": "connexion refusée"}
            result = ask("Quel est le prix du bitcoin ?")
        self.assertEqual(result.level, "offbase")

    def test_offbase_on_llm_exception(self):
        with patch('chatbot.engine.llm_client.check_availability') as mock_check, \
             patch('chatbot.engine.llm_client.generate') as mock_gen:
            mock_check.return_value = {"available": True, "model": "phi3:mini", "error": None}
            mock_gen.side_effect = ConnectionError("Ollama crashé")
            result = ask("Quel est le prix du bitcoin ?")
        self.assertIn(result.level, ["offbase", "llm"])
        # Si level=offbase, la réponse doit contenir le message de refus
        if result.level == "offbase":
            self.assertIn("secrétariat", result.answer)
```

---

## 9. Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-dev-key` | Clé secrète Django — **obligatoire en prod** |
| `DEBUG` | `False` | Activer uniquement en développement |
| `ALLOWED_HOSTS` | — | Domaines autorisés, séparés par des virgules |
| `DATABASE_URL` | SQLite local | URL PostgreSQL Railway ou serveur dédié |
| `TRANSFORMERS_OFFLINE` | `1` | Force HuggingFace en mode hors ligne |
| `HF_DATASETS_OFFLINE` | `1` | Idem pour les datasets HF |
| `SCORE_DIRECT` | `0.55` | Seuil FAISS — niveau 2 DIRECT |
| `SCORE_LLM` | `0.30` | Seuil FAISS — en dessous → niveau 4 LLM |
| `RAG_DATA_DIR` | `backend/rag_data` | Chemin vers `index.bin` et `metadata.json` |
| `TFIDF_CACHE_PATH` | `rag_data/tfidf_cache.pkl` | Chemin vers le cache TF-IDF |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL du serveur Ollama |
| `OLLAMA_MODEL` | `phi3:mini` | Modèle Ollama pour le niveau LLM |
| `OLLAMA_READ_TIMEOUT` | `180` | Timeout de lecture Ollama en secondes |
| `OLLAMA_CONNECT_TIMEOUT` | `5` | Timeout de connexion TCP Ollama |
| `REDIS_URL` | — | URL Redis pour le cache Django (si activé) |

---

*Club Informatique SUP'PTIC — Documentation technique Gen 3 — Mai 2026*