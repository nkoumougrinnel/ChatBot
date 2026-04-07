# ChatBot SUP'PTIC – Phase 2

**Réalisé par :** Club Informatique SUP'PTIC

---

## Passage à la Phase 2

Le projet a maintenant quitté la Phase 1 pour entrer en **Phase 2**. Les documents de la Phase 1 restent disponibles dans `docs/phase1/` à titre historique, mais l'activité principale se concentre désormais sur :

- `docs/phase2/architecture/`
- `docs/phase2/documentation_technique/`
- `docs/phase2/roadmap/`

---

## Présentation

Ce **ChatBot SUP'PTIC** est désormais en **Phase 2**, avec une évolution majeure vers une architecture RAG (Retrieval-Augmented Generation). Le projet conserve les bases du chatbot FAQ, mais ajoute :

- une architecture hybride RAG + TF-IDF
- un index FAISS pour la recherche vectorielle
- un LLM local via Ollama pour enrichir les réponses
- une interface plus riche avec historique de conversation

---

## Fonctionnalités principales

| Fonctionnalité           | Description                                                                    |
| ------------------------ | ------------------------------------------------------------------------------ |
| Pipeline RAG             | Recherche de documents par embeddings MiniLM, index FAISS, puis génération LLM |
| Bascule RAG / TF-IDF     | Passage automatique entre RAG et TF-IDF selon le score de confiance            |
| API REST v2              | Endpoint `/api/chatbot/ask/` amélioré avec fallback, sources et méthode        |
| Historique conversation  | Stockage local (localStorage) des conversations et navigation multi-tours      |
| Retour utilisateur       | Feedback positif/négatif avec traçage de la méthode utilisée (RAG ou TF-IDF)   |
| Passage au React         | Interface web migrée vers React, chat responsive, badge de méthode et streaming SSE |

---

## Architecture du projet

Le dépôt est organisé ainsi :

- `backend/` : application Django, API, gestion des FAQ et du moteur de similarité
- `frontend/` : interface utilisateur et application PWA
- `data/` : jeux de données, scripts et documentation de données
- `docs/` : documentation générale et par phase
- `requirements.txt` : dépendances Python

---

## Documentation Phase 2

La documentation de la Phase 2 est le bon point d'entrée :

- `docs/phase2/README.md` : résumé de la Phase 2
- `docs/phase2/architecture/` : documents d'architecture système
- `docs/phase2/documentation_technique/` : documentation technique
- `docs/phase2/roadmap/` : feuille de route Phase 2

Pour les éléments de configuration et de déploiement, consultez également :

- `docs/setup/NGROK_SETUP.md`
- `backend/doc/` : spécifications backend détaillées
- `frontend/README.md` : documentation frontend

---

## Installation rapide

1. Créez et activez un environnement virtuel :
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. Installez les dépendances :
   ```powershell
   pip install -r requirements.txt
   ```
3. Lancez le serveur Django :
   ```powershell
   python backend/manage.py runserver
   ```
4. Ouvrez `http://localhost:8000/` dans votre navigateur.

---

## Notes

- Le contenu principal de la Phase 2 est dans `docs/phase2/`.
- Les documents de la Phase 1 sont conservés dans `docs/phase1/` pour référence historique.
- Vérifiez l'encodage UTF-8 si vous éditez des fichiers de documentation.
