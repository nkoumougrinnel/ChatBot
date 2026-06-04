# Backend Django — SUP'ONE AI

> Guide complet (installation, déploiement Railway, variables d’environnement) : **[../docs/GUIDE_COMPLET.md](../docs/GUIDE_COMPLET.md)**

## Démarrage rapide

```powershell
cd backend
$env:DEBUG="True"
pip install -r ../requirements.txt
python manage.py setup_demo
python manage.py runserver
```

- API : http://127.0.0.1:8000/api/health/
- Chat Phase 1 : `POST /api/chatbot/ask/`
- Pipeline Gen3 (optionnel) : `POST /api/v2/chatbot/ask/`

## Pipeline RAG Gen3

```powershell
pip install faiss-cpu sentence-transformers google-generativeai
# Ajoutez GEMINI_API_KEY dans .env pour le niveau LLM
python manage.py setup_gen3 --allow-download
python manage.py runserver
```

| Commande | Description |
|----------|-------------|
| `python manage.py setup_gen3` | Phase 1 + index FAISS + cache TF-IDF Gen3 |
| `python manage.py build_rag_index` | Construit `rag_data/index.bin` |
| `python manage.py check_gen3` | Diagnostic FAISS / TF-IDF / Gemini |
| `python manage.py setup_demo` | Migrations + fixtures + index TF-IDF Phase 1 |
| `python manage.py rebuild_vectors` | Recalcule les vecteurs Phase 1 |
| `python manage.py test` | Tests unitaires |

API Gen3 : `POST /api/v2/chatbot/ask/` (SSE), `GET /api/v2/chatbot/status/`

## Frontend React

En développement, le frontend Vite (`frontend/app`, port **5173**) proxifie `/api` vers ce serveur.  
`DEBUG=True` active CORS pour toutes les origines locales.
