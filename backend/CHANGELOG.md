# CHANGELOG.md — ChatBot SUP'ONE

Toutes les modifications notables du projet sont documentées dans ce fichier.  
Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

---

## [2.0.0] — Avril 2026 — Phase 2 RAG

### Ajouté

#### Pipeline RAG
- `chatbot/engine/embedder.py` — Vectorisation sémantique avec `all-MiniLM-L6-v2` (384 dimensions, normalisé)
- `chatbot/engine/faiss_search.py` — Index vectoriel FAISS (`IndexFlatIP`), chargement au démarrage Django via `AppConfig.ready()`, rechargement à chaud sans redémarrage
- `chatbot/engine/llm_client.py` — Client HTTP Ollama (Phi-3 Mini), modes génération complète et streaming token par token
- `chatbot/engine/prompt_builder.py` — Construction du prompt Phi-3 avec historique conversationnel (3 derniers échanges) et contextes FAISS
- `chatbot/engine/rag_pipeline.py` — Orchestrateur principal : embed → FAISS → seuil → LLM ou TF-IDF, expose `ask()` et `ask_stream()`
- `chatbot/engine/tfidf_fallback.py` — Encapsulation du moteur TF-IDF Phase 1 comme fallback automatique

#### Bascule automatique RAG ↔ TF-IDF
- Score FAISS ≥ 0.55 → pipeline RAG complet (LLM appelé)
- Score FAISS ∈ [0.50, 0.55[ → RAG avec avertissement de confiance modérée
- Score FAISS < 0.50 → fallback TF-IDF Phase 1 (réponse immédiate)

#### Streaming SSE
- Endpoint `POST /api/chatbot/ask/` avec paramètre `stream: true`
- Format SSE : événements `meta`, `token`, `done`
- Header `X-Accel-Buffering: no` pour compatibilité Nginx

#### Nouveaux endpoints API
- `POST /api/chatbot/ask/` — Pipeline RAG v2 (remplace l'endpoint Phase 1)
- `POST /api/feedback/` — Enregistrement like/dislike avec champ `rag_method`
- `GET  /api/stats/rag/` — Statistiques d'usage et état de l'index FAISS
- `POST /api/reload-index/` — Rechargement FAISS à chaud sans redémarrer Django

#### Scripts utilitaires
- `scripts/build_index.py` — Génère `index.bin` et `metadata.json` depuis les fichiers JSON v2
- `scripts/import_json.py` — Import des fichiers JSON en base Django sans doublons (compatibilité format Phase 1 et Phase 2)
- `scripts/reload_trigger.py` — Déclencheur de rechargement FAISS via fichier sentinel
- `scripts/verify_quota.py` — Vérification des quotas journaliers de l'équipe Data

#### Tests unitaires
- `chatbot/tests/test_embedder.py` — 9 tests : forme, dtype, norme, similarité sémantique, latence
- `chatbot/tests/test_faiss_search.py` — 11 tests : chargement, recherche, cohérence sur 20 questions, robustesse
- `chatbot/tests/test_fallback.py` — 13 tests : bascule automatique, questions hors domaine, interface RAG pipeline

#### Modèle de données
- Champ `source` ajouté au modèle `FAQ` (provenance de la réponse)
- Champ `rag_method` ajouté au modèle `Feedback` (méthode ayant produit la réponse : RAG ou TF-IDF)
- Champ `embedding_id` ajouté au modèle `FAQ` (référence dans l'index FAISS)

#### Documentation
- `FLUX_RAG.md` — Pipeline RAG étape par étape
- `OLLAMA_SETUP.md` — Guide d'installation et configuration Ollama
- `CHANGELOG.md` — Ce fichier
- `README.md` — Mise à jour section Phase 2

### Modifié

- `chatbot/views.py` — Refonte complète : suppression de `ChatbotAskViewSet`, ajout des 4 nouvelles vues `@api_view`
- `urls.py` — Suppression de `ChatbotAskViewSet` du router DRF, ajout des routes Phase 2 via `path()`
- `requirements.txt` — Ajout : `sentence-transformers`, `faiss-cpu`, `scikit-learn` (déjà présent Phase 1)
- `settings.py` — Ajout `TRANSFORMERS_OFFLINE=1` et `HF_DATASETS_OFFLINE=1` pour le mode hors ligne

### Corrigé

- `prompt_builder.py` — Suppression de la variable morte `user_turn` contenant `chr(10).join()` dans une f-string (SyntaxError silencieuse)
- `rag_pipeline.py` — Déplacement du `sys.path.insert()` avant les imports relatifs (ImportError en mode standalone)
- `tfidf_fallback.py` — Gestion du BOM UTF-8 (`utf-8-sig`), correction encodage Latin-1 → UTF-8 (`Ã©` → `é`), compatibilité format JSON Phase 1 et Phase 2
- `llm_client.py` — Timeout configurable via `RAG_LLM_TIMEOUT` (défaut 60s au lieu de 120s)

### Supprimé

- `ChatbotAskViewSet` retiré du router DRF (remplacé par `ask_chatbot` Phase 2)
- Dépendance à `intent_detection.py` et `train_intents.py` dans `views.py` (remplacée par le pipeline RAG)

---

## [1.0.0] — Février 2026 — Phase 1 TF-IDF

### Ajouté

- Recherche TF-IDF + similarité cosinus
- Base de données Django avec modèles `FAQ`, `Category`, `Feedback`
- API REST (5 endpoints documentés)
- Interface PWA (HTML/CSS/JS)
- Système de feedback et statistiques
- Détection d'intent par classification

### Limites identifiées

- Recherche par mots exacts uniquement (pas de compréhension sémantique)
- Réponses brutes sans adaptation au contexte
- Pas de mémoire conversationnelle
- Dataset insuffisant (< 500 Q/R)

---

*Document produit par l'équipe Backend — Club Informatique SUP'PTIC*
