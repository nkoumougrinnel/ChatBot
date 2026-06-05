# ChatBot SUP'PTIC — Assistant FAQ intelligent (SUP'ONE)

Assistant conversationnel pour l'**École Supérieure des Postes, Télécommunications
et Technologies de l'Information et de la Communication (SUP'PTIC)**, développé par
le Club Informatique. Il répond aux questions fréquentes des étudiants et du
personnel à partir d'une base de FAQ, via un backend Django REST et un frontend web.

---

## Présentation

Le projet combine deux approches de recherche de réponse :

1. **Phase 1 — Recherche TF-IDF** (`faq` + `chatbot`) : vectorisation TF-IDF des
   questions et similarité cosinus sur la base FAQ stockée en base de données.
   Exposée sous `/api/`.
2. **Gen3 — Pipeline RAG** (`chatbot/engine`) : pipeline à 4 niveaux
   (règles conversationnelles → recherche sémantique FAISS → repli TF-IDF →
   génération LLM via Google Gemini). Exposé sous `/api/v2/`.

Le pipeline Gen3 dépend de bibliothèques optionnelles. S'il ne peut pas être
chargé (dépendances ou artefacts absents), **l'API Phase 1 reste pleinement
fonctionnelle**.

---

## Fonctionnalités

| Fonctionnalité | Description |
| --- | --- |
| Recherche TF-IDF | Similarité cosinus sur la base FAQ, recherche par catégories optimisée pour la RAM |
| Pipeline RAG Gen3 | FAISS (embeddings MiniLM) + repli TF-IDF + génération Gemini, en streaming SSE |
| API REST | Endpoints pour interroger, gérer les FAQ et collecter des statistiques |
| Interface web (PWA) | Chat interactif (`frontend/advanced_chat/`), responsive, hors-ligne |
| Feedback utilisateur | Like / dislike + commentaire, ajustant la popularité et les scores |
| Statistiques | Suivi de la satisfaction et des FAQ populaires |

---

## Architecture du projet

```
ChatBot/
├── backend/
│   ├── config/            # Réglages Django (settings, urls, wsgi, asgi)
│   ├── faq/               # FAQ, catégories, feedback + API Phase 1 (/api/)
│   ├── chatbot/           # Prétraitement, TF-IDF, similarité
│   │   └── engine/        # Pipeline RAG Gen3 (FAISS, Gemini, TF-IDF) → /api/v2/
│   ├── users/             # Modèle utilisateur personnalisé
│   ├── data/              # JSON (règles conversationnelles, bases) + scripts
│   ├── manage.py
│   ├── Procfile / runtime.txt
│   └── requirements.txt   # -> pointe vers le requirements.txt racine
│
├── frontend/
│   ├── app/               # React + Vite + PWA + APK Android (recommandé)
│   ├── index.html, app.js # Démo simple
│   └── advanced_chat/     # PWA vanilla JS (historique)
│
├── data/                  # Corpus CSV / JSON
├── docs/                  # Documentation technique (backend, API)
├── .env.example           # Modèle de configuration d'environnement
├── requirements.txt       # Dépendances (fichier canonique)
└── README.md
```

---

## Prérequis

- Python 3.10+
- Node.js 18+ (frontend React)
- pip et virtualenv
- (Optionnel, pour Gen3) clé API Google Gemini
- (APK Android) JDK 21 + Android SDK — voir le guide complet

---

## Démarrage rapide

```powershell
git clone <repository-url>
cd ChatBot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

cd backend
python manage.py setup_demo
python manage.py runserver 127.0.0.1:8001
```

Dans un second terminal :

```powershell
cd frontend\app
npm install
npm run dev
```

- **API** : http://127.0.0.1:8001/api/health/
- **Frontend** : http://localhost:5174

> **Documentation complète** (installation, Gen3, déploiement Railway/Netlify, APK Android, dépannage) : **[docs/GUIDE_COMPLET.md](docs/GUIDE_COMPLET.md)**

### Variables d'environnement

Toutes les variables sont décrites dans [`.env.example`](.env.example). En
développement, définissez `DEBUG=True`. En production, `SECRET_KEY` est
**obligatoire** (le serveur refuse de démarrer sans elle quand `DEBUG=False`).

---

## API REST

### Phase 1 — `/api/`

| Méthode | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/chatbot/ask/` | Poser une question → top-k résultats TF-IDF + scores |
| `GET` | `/api/faq/` | Lister les FAQ (paginé) |
| `GET` | `/api/categories/` | Lister les catégories |
| `POST` | `/api/feedback/` | Enregistrer un feedback (like/dislike) |
| `GET` | `/api/stats/` | Statistiques de satisfaction |

### Gen3 (RAG) — `/api/v2/`

| Méthode | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v2/chatbot/status/` | État du LLM (Gemini) et du pipeline |
| `POST` | `/api/v2/chatbot/ask/` | Question via le pipeline RAG (SSE ou JSON) |
| `POST` | `/api/v2/chatbot/test-llm/` | Mesure de latence LLM (debug) |
| `GET` | `/api/v2/chatbot/reload-index/` | Recharge l'index FAISS à chaud |

**Exemple :**

```bash
curl -X POST http://localhost:8001/api/chatbot/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Quand sont les examens ?", "top_k": 3}'
```

```json
{
  "question": "Quand sont les examens ?",
  "results": [
    { "faq_id": 1, "question": "...", "answer": "...", "category": "Examens", "score": 0.92 }
  ],
  "count": 1,
  "status": "confident"
}
```

---

## Tests

```bash
cd backend
python manage.py test
```

La suite couvre les modèles, le signal de feedback et les endpoints de l'app
`faq`, ainsi que les fonctions de recherche de l'app `chatbot`.

---

## Déploiement

| Composant | Plateforme | Fichiers |
|-----------|------------|----------|
| Backend API | **Railway** (Gunicorn + Postgres) | `railway.json`, `nixpacks.toml`, `deploy/railway.env.example` |
| Frontend PWA | **Netlify** ou Vercel | `frontend/app/netlify.toml`, `deploy/netlify.env.example` |
| Application Android | Build local (Capacitor) | [docs/MOBILE.md](docs/MOBILE.md) |
| CI | GitHub Actions | `.github/workflows/ci.yml` |

**Procédure pas à pas** : **[docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md)**

---

## Documentation

| Document | Description |
|----------|-------------|
| **[docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md)** | Mise en production (Railway + Netlify) |
| **[docs/GUIDE_COMPLET.md](docs/GUIDE_COMPLET.md)** | Guide d’exécution locale et configuration |
| **[docs/MOBILE.md](docs/MOBILE.md)** | Application Android (APK Capacitor) |
| [frontend/app/README.md](frontend/app/README.md) | Frontend React, PWA, build APK |
| [docs/README.md](docs/README.md) | Index de la documentation |
| [docs/backend/](docs/backend/) | Architecture, API, tests |
| [backend/chatbot/engine/README.md](backend/chatbot/engine/README.md) | Pipeline RAG Gen3 |

---

## Crédits

Développé par le **Club Informatique SUP'PTIC**.
