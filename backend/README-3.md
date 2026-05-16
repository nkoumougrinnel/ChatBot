# ChatBot SUP'ONE — Phase 2

> **Assistant intelligent du Club Informatique de SUP'PTIC**  
> Pipeline RAG · MiniLM · FAISS · Ollama (Phi-3 Mini) · React Mobile  
> Version 2.0.0 — Avril 2026

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Architecture](#2-architecture)
3. [Installation](#3-installation)
4. [Démarrage rapide](#4-démarrage-rapide)
5. [Endpoints API](#5-endpoints-api)
6. [Structure du projet](#6-structure-du-projet)
7. [Scripts utilitaires](#7-scripts-utilitaires)
8. [Tests](#8-tests)
9. [Variables d'environnement](#9-variables-denvironnement)
10. [Équipe](#10-équipe)

---

## 1. Présentation

SUP'ONE est le chatbot intelligent de SUP'PTIC (École Nationale Supérieure des Postes, Télécommunications et TIC du Cameroun). La Phase 2 remplace le moteur TF-IDF de la Phase 1 par un pipeline RAG complet fonctionnant entièrement en local, sans connexion internet ni coût d'API.

### Comparaison Phase 1 → Phase 2

| Critère | Phase 1 | Phase 2 |
|---|---|---|
| Recherche | Mots exacts (TF-IDF) | Sens sémantique (MiniLM) |
| Génération | Réponse pré-écrite | Réponse générée par Phi-3 |
| Mémoire | Aucune | 3 derniers échanges |
| Bascule | — | Automatique RAG ↔ TF-IDF |
| Interface | PWA HTML/CSS | React Mobile |
| Dataset | ~450 Q/R | 1500+ Q/R |

### Pipeline RAG

```
Question → MiniLM (embed) → FAISS (top-3) → Score ≥ 0.55 ?
                                                  │
                                    Oui → Phi-3 via Ollama → Réponse naturelle
                                    Non → TF-IDF Phase 1  → Réponse directe
```

---

## 2. Architecture

```
ChatBot/
├── backend/                      # Django + Pipeline RAG
│   ├── chatbot/
│   │   ├── engine/               # Cœur du système RAG
│   │   │   ├── embedder.py       # Vectorisation MiniLM
│   │   │   ├── faiss_search.py   # Recherche vectorielle FAISS
│   │   │   ├── llm_client.py     # Client Ollama Phi-3
│   │   │   ├── prompt_builder.py # Construction prompt
│   │   │   ├── rag_pipeline.py   # Orchestrateur principal
│   │   │   └── tfidf_fallback.py # Fallback TF-IDF
│   │   ├── tests/
│   │   │   ├── test_embedder.py
│   │   │   ├── test_faiss_search.py
│   │   │   └── test_fallback.py
│   │   ├── views.py              # Endpoints Django
│   │   └── apps.py               # Chargement FAISS au démarrage
│   ├── scripts/
│   │   ├── build_index.py        # Génère index FAISS
│   │   ├── import_json.py        # Import FAQ en base
│   │   ├── reload_trigger.py     # Reload FAISS à chaud
│   │   └── verify_quota.py       # Vérification quotas Data
│   └── rag_data/
│       ├── index.bin             # Index FAISS (généré)
│       ├── metadata.json         # Mapping vecteurs (généré)
│       └── tfidf_cache.pkl       # Cache TF-IDF (généré)
├── data/                         # Fichiers JSON FAQ (équipe Data)
│   ├── faq_admissions.json
│   ├── faq_frais.json
│   └── ...
└── supptic-chat/                 # Frontend React Mobile
```

---

## 3. Installation

### Prérequis

- Python 3.10+
- pip
- Ollama installé ([ollama.com/download](https://ollama.com/download))

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/nkoumougrinnel/ChatBot.git
cd ChatBot

# 2. Créer et activer l'environnement virtuel
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 3. Installer les dépendances Python
pip install -r backend/requirements.txt

# 4. Télécharger le modèle Phi-3 (une seule fois, ~2.4 Go)
ollama pull phi3:mini

# 5. Appliquer les migrations Django
cd backend
python manage.py migrate

# 6. Construire l'index FAISS
python scripts/build_index.py --data-dir ../data
```

---

## 4. Démarrage rapide

```bash
# Terminal 1 — Démarrer Ollama
ollama serve

# Terminal 2 — Démarrer Django
cd backend
python manage.py runserver
```

Tester que tout fonctionne :

```bash
curl -X POST http://localhost:8000/api/chatbot/ask/ \
     -H "Content-Type: application/json" \
     -d '{"question": "Quels sont les frais de scolarité ?", "stream": false}'
```

Réponse attendue :

```json
{
  "answer": "Les frais de scolarité à SUP'PTIC s'élèvent à...",
  "sources": [{"question": "...", "score": 0.87, "categorie": "Admissions"}],
  "method": "RAG",
  "best_score": 0.87
}
```

---

## 5. Endpoints API

### `POST /api/chatbot/ask/`

Endpoint principal du chatbot.

**Corps de la requête :**

```json
{
  "question": "C'est combien pour s'inscrire ?",
  "stream":   false,
  "history": [
    {"role": "user",      "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"}
  ]
}
```

**Réponse sans streaming :**

```json
{
  "answer":     "Les frais de scolarité s'élèvent à 525 000 FCFA...",
  "sources":    [{"question": "...", "score": 0.87, "categorie": "Admissions", "source": "..."}],
  "method":     "RAG",
  "best_score": 0.87
}
```

**Réponse avec streaming (`stream: true`) :**

```
Content-Type: text/event-stream

data: {"type": "meta",  "method": "RAG", "best_score": 0.87, "sources": [...]}\n\n
data: {"type": "token", "content": "Les "}\n\n
data: {"type": "token", "content": "frais..."}\n\n
data: {"type": "done"}\n\n
```

---

### `POST /api/feedback/`

Enregistrer un like ou dislike.

```json
{
  "message_id": "abc123",
  "type":       "like",
  "method":     "RAG"
}
```

Réponse : `{"status": "ok"}`

---

### `GET /api/stats/rag/`

Statistiques d'usage.

```json
{
  "total_feedbacks": 142,
  "rag_count":       98,
  "tfidf_count":     44,
  "likes":           87,
  "dislikes":        12,
  "index_stats":     {"ntotal": 1050, "dim": 384, "loaded": true}
}
```

---

### `POST /api/reload-index/`

Recharger l'index FAISS à chaud après un rebuild.

```json
{"status": "ok", "message": "Index rechargé : 1050 vecteurs"}
```

---

## 6. Structure du projet

### Branches Git

| Branche | Équipe | Contenu |
|---|---|---|
| `main` | — | Version stable livrée |
| `dev` | Toutes | Intégration continue |
| `backend` | Backend | Pipeline RAG + API |
| `frontend` | Frontend | Application React |
| `data` | Data | Fichiers JSON FAQ |
| `database` | BD | Migrations + scripts |

### Format JSON FAQ (v2)

```json
{
  "id":              "faq_001",
  "categorie":       "Admissions",
  "sous_theme":      "Frais de scolarité",
  "question":        "Quels sont les frais de scolarité ?",
  "reponse_enrichie": "Les frais s'élèvent à 525 000 FCFA...",
  "exemples": [
    "C'est combien pour s'inscrire ?",
    "Combien coûte la scolarité à SUP'PTIC ?"
  ],
  "sources": ["e-supptic.cm"],
  "valide": true
}
```

---

## 7. Scripts utilitaires

### Construire l'index FAISS

```bash
python scripts/build_index.py --data-dir ../data
```

### Importer les FAQ en base

```bash
python scripts/import_json.py --file ../data/faq_admissions.json
python scripts/import_json.py --dir ../data/
```

### Recharger l'index à chaud

```bash
python scripts/reload_trigger.py
```

### Vérifier les quotas Data

```bash
python scripts/verify_quota.py --file ../data/faq_admissions_j1.json --quota 70
```

---

## 8. Tests

```bash
cd backend

# Tests individuels
python manage.py test chatbot.tests.test_embedder
python manage.py test chatbot.tests.test_faiss_search
python manage.py test chatbot.tests.test_fallback

# Tous les tests d'un coup
python manage.py test chatbot.tests
```

Résultat attendu :

```
Ran 33 tests in ~15.XXXs
OK
```

---

## 9. Variables d'environnement

Créer un fichier `.env` à la racine du projet :

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings
SECRET_KEY=your-secret-key

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
RAG_LLM_TIMEOUT=60

# Pipeline RAG
RAG_SCORE_HIGH=0.55
RAG_SCORE_MED=0.50
RAG_TOP_K=3

# HuggingFace hors ligne
TRANSFORMERS_OFFLINE=1
HF_DATASETS_OFFLINE=1

# Chemins
RAG_DATA_DIR=backend/rag_data
FAQ_DATA_DIR=data/
```

---

## 10. Équipe

| Rôle | Équipe | Mission |
|---|---|---|
| Pipeline RAG | Backend (3) | MiniLM, FAISS, Ollama, API |
| Base de données | BD (1) | Migrations, imports, cohérence |
| Données FAQ | Data (4) | Collecte et validation Q/R |
| Interface React | Frontend (2) | App mobile, streaming, UX |

**Encadrant** : Dr. Nzebop  
**Chef de projet** : NKOUMOU TJADE, Chef de la Division de Programmation  
**Institution** : Club Informatique SUP'PTIC  

---

## Documentation complémentaire

- [`FLUX_RAG.md`](./FLUX_RAG.md) — Pipeline RAG étape par étape
- [`OLLAMA_SETUP.md`](./OLLAMA_SETUP.md) — Installation et configuration Ollama
- [`CHANGELOG.md`](./CHANGELOG.md) — Journal des modifications
- [`backend/chatbot/engine/README.md`](./backend/chatbot/engine/README.md) — Documentation des modules engine/

---

*Club Informatique SUP'PTIC — Phase 2 — Avril 2026*
