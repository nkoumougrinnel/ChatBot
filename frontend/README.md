# Frontend - Interfaces Utilisateur

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

