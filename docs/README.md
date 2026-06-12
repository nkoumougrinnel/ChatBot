# Documentation — ChatBot SUP'ONE AI

## Guide principal

**[GUIDE_COMPLET.md](GUIDE_COMPLET.md)** — Installation locale, configuration, exécution, tests, dépannage.

**[DEPLOIEMENT.md](DEPLOIEMENT.md)** — **Mise en production** : Railway (backend), Netlify/Vercel (frontend PWA), CI GitHub, checklist.

**[DOCKER.md](DOCKER.md)** — **Serveur Docker** : Compose (Postgres + API + Nginx), volumes, bootstrap, HTTPS.

**[MOBILE.md](MOBILE.md)** — Application Android (Capacitor) : build APK, `VITE_API_URL`, thèmes clair/sombre, clavier, checklist distribution.

**Présentation PowerPoint** — [`SUPONE_AI_Club_Informatique_SUPPTIC.pptx`](SUPONE_AI_Club_Informatique_SUPPTIC.pptx) (générée via `scripts/generate_presentation.py`).

## Documentation technique backend

| Fichier | Sujet |
|---------|--------|
| [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md) | Architecture Django et modules |
| [backend/API_REST_IMPLEMENTATION.md](backend/API_REST_IMPLEMENTATION.md) | Implémentation API REST |
| [backend/API_TEST_GUIDE.md](backend/API_TEST_GUIDE.md) | Guide de tests API |
| [backend/TEST_PIPELINE.md](backend/TEST_PIPELINE.md) | Tests du pipeline |
| [backend/INTENTS.md](backend/INTENTS.md) | Intents conversationnels |
| [backend/PREPROCESSING_COMPARAISON.md](backend/PREPROCESSING_COMPARAISON.md) | Comparaison prétraitement |

## Autres README

- [README racine](../README.md) — Vue d’ensemble du dépôt
- [backend/README.md](../backend/README.md) — Démarrage rapide backend
- [frontend/app/README.md](../frontend/app/README.md) — Frontend React et APK
