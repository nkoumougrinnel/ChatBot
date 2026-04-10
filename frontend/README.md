<<<<<<< HEAD
README — frontend/

Ce dossier contient un mini-frontend de test (HTML + JS) pour se connecter
à l'API chatbot. Il sert d'exemple rapide pour l'équipe Frontend.

Fichiers principaux:

- `simple_chat.html` : mini-app qui envoie une requête POST à `/api/chatbot/ask/` et affiche les résultats.
- `README.md` (ce fichier) : instructions pour lancer et tester.

Comment utiliser :

1. Démarrer le serveur Django :

```powershell
cd C:\Users\DELL\Desktop\ChatBot
.venv\Scripts\Activate.ps1
python backend/manage.py runserver
```

2. Servir le frontend temporairement (optionnel, utile pour éviter les issues CORS) :

```powershell
# depuis la racine du repo
python -m http.server 8001
# ouvrir http://localhost:8001/frontend/simple_chat.html
```

3. Ouvrir `frontend/simple_chat.html` dans le navigateur (ou via le serveur HTTP ci-dessus).

Notes :

- Le fichier est prévu pour un usage développement local uniquement.
- Si vous servez la page depuis un hôte différent du backend, configurez CORS côté backend.

Erreurs courantes :

- `TypeError: Failed to fetch` : serveur backend non démarré ou CORS refusé.
- `400/500` : montreront le message d'erreur renvoyé par l'API dans la zone "status".

Sécurité : Ne pas déployer ce fichier en production sans contrôles (CORS, auth, rate limit).
=======
﻿# Frontend - Interfaces Utilisateur

Ce dossier contient les interfaces utilisateur du projet ChatBot.

## Structure

- `pwa/` - Application PWA existante (Progressive Web App)
  - Interface HTML5 responsive
  - Support du feedback utilisateur
  - Statistiques en temps réel
  - Mode hors ligne

- `react-app/` - Nouvelle application React (en développement)
  - Framework React moderne
  - Composants réutilisables
  - Intégration avec le moteur RAG Phase 2

## Déploiement

### PWA (Production actuelle)

```bash
python start_server.py
# Interface disponible sur http://localhost:3000
```

Le serveur pointe automatiquement vers le dossier `pwa/`.

### Configuration Netlify

- `netlify.toml` - Configuration de déploiement
- Support pour les deux applications

## Développement

### PWA

- Technologies : HTML5, CSS3, JavaScript (ES6+)
- Backend : API REST Django
- Fonctionnalités : Chat, feedback, statistiques

### React App

- Technologies : React, Vite (prévu)
- Backend : API REST Django + moteur RAG
- Fonctionnalités : Interface moderne avec RAG avancé

## Migration

La PWA actuelle sera maintenue pendant la transition vers React. Les deux interfaces coexisteront jusqu'à  la finalisation de la Phase 2.

- Les statistiques chargées

### Network Tab

Vérifiez dans les outils de dev (F12 â†’ Network):

- âœ… `POST /api/chatbot/ask/` - Succès 200
- âœ… `POST /api/feedback/` - Succès 201
- âœ… `GET /api/stats/` - Succès 200

>>>>>>> 5d3964364534cdcbb97c8d55151f3aac0b45f482
