# PWA - Progressive Web App

Interface de chatbot avancée pour SUP'PTIC sous forme d'application web progressive.

## Fonctionnalités

### Chat

- Interface conversationnelle fluide
- Recherche dans la FAQ via similarité TF-IDF
- Affichage progressif des réponses (effet de "typing")
- Sélection du nombre de résultats (top-k: 1, 3, 5)

### Feedback Utilisateur

- Like/Dislike des réponses
- Copie dans le presse-papiers
- Partage des réponses

### Statistiques

- Panel de statistiques des FAQs
- Score moyen basé sur les feedbacks
- Nombre total de feedbacks par FAQ
- Mise à  jour en temps réel

## Structure

```
pwa/
â”œâ”€â”€ index.html         # Page principale
â”œâ”€â”€ demo.html          # Page de démonstration
â”œâ”€â”€ offline.html       # Page hors ligne
â”œâ”€â”€ manifest.json      # Manifest PWA
â”œâ”€â”€ service-worker.js  # Service worker
â”œâ”€â”€ css/
â”‚   â””â”€â”€ styles.css     # Styles et animations
â”œâ”€â”€ js/
â”‚   â””â”€â”€ main.js        # Logique JavaScript
â””â”€â”€ icons/             # Icônes PWA
```

## Installation PWA

1. Ouvrir `index.html` dans un navigateur moderne
2. Cliquer sur "Installer" dans la barre d'adresse
3. L'application s'installe comme une app native

## Utilisation

### Lancement local

```bash
cd frontend
python start_server.py
# Accessible sur http://localhost:3000
```

### Architecture API

| Endpoint            | Méthode | Description                     |
|---------------------|---------|---------------------------------|
| `/api/chatbot/ask/` | POST    | Questions et FAQs pertinentes   |
| `/api/feedback/`    | POST    | Feedback positif/négatif        |
| `/api/stats/`       | GET     | Statistiques des FAQs          |

## Technologies

- HTML5, CSS3, JavaScript ES6+
- Service Worker pour le mode hors ligne
- Web App Manifest
- API Fetch pour les appels backend
- Responsive design

## Mode hors ligne

La PWA fonctionne partiellement hors ligne :

- Page d'accueil accessible
- Interface de base fonctionnelle
- Message d'indisponibilité pour les fonctionnalités réseau

## Personnalisation

### Couleurs

Variables CSS dans `:root` :

- Primaire: `#1a4594` (bleu SUP'PTIC)
- Accent: `#60a5fa` (bleu clair)
- Succès: `#10b981` (vert)
- Avertissement: `#f59e0b` (orange)

### Messages d'accueil

Modifiables dans `.welcome-message` de `index.html`

### Suggestions

Modifiables dans `.suggestion-card`

## Débogage

Consulter la console du navigateur (F12) pour :

- Logs d'initialisation
- Appels API
- Erreurs de feedback

## Migration

Cette PWA sera maintenue pendant la transition vers l'application React dans `../react-app/`.

