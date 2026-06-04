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
│   ├── index.html, app.js, style.css   # Démo simple
│   └── advanced_chat/     # Application PWA (main.js, styles.css, service-worker…)
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
- pip et virtualenv
- (Optionnel, pour Gen3) une clé API Google Gemini

---

## Installation et lancement

```powershell
# 1. Cloner et créer l'environnement virtuel
git clone <repository-url>
cd ChatBot
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # (Linux/macOS : source .venv/bin/activate)

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
copy .env.example .env            # puis éditer .env (SECRET_KEY, GEMINI_API_KEY…)

# 4. Initialiser la base de données
cd backend
python manage.py migrate

# 5. (Optionnel) Charger des données de démonstration
python manage.py loaddata faq/fixtures/*.json

# 6. Lancer le serveur de développement
python manage.py runserver
```

- **API** : http://localhost:8000/api/
- **Frontend** : ouvrir `frontend/advanced_chat/index.html` (ou servir le dossier).

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
curl -X POST http://localhost:8000/api/chatbot/ask/ \
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

Le projet est prêt pour un déploiement de type **Railway / Gunicorn + WhiteNoise** :

- `requirements.txt` (racine) : dépendances installées au build.
- `railway.json` / `Procfile` : commande de démarrage Gunicorn.
- Définir au minimum `SECRET_KEY`, `DEBUG=False`, `DATABASE_URL` et
  `CORS_ALLOWED_ORIGINS` ; `GEMINI_API_KEY` pour activer le niveau LLM.

---

## Documentation complémentaire

- `docs/backend/` : architecture, API, intents, pipeline de tests.
- `backend/chatbot/engine/README.md` : détail du pipeline RAG Gen3.

---

## Crédits

Développé par le **Club Informatique SUP'PTIC**.
