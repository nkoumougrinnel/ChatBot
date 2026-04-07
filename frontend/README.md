# Advanced Chat - Interface de Chatbot Avancée

## 📌 Vue d'ensemble

Interface HTML5 moderne et responsive pour le chatbot SUP'PTIC avec support complet de la fonctionnalité de **feedback** implémentée en backend.

## ✨ Fonctionnalités

### Chat

- 💬 Interface conversationnelle fluide
- 🔍 Recherche dans la FAQ via similarité TF-IDF
- ⚡ Affichage progressif des réponses (effet de "typing")
- 📊 Sélection du nombre de résultats (top-k: 1, 3, 5)

### Feedback Utilisateur

- 👍 **Like** - Marquer une réponse comme utile
- 👎 **Dislike** - Marquer une réponse comme peu utile
- 📋 **Copy** - Copier la réponse dans le presse-papiers
- 📤 **Share** - Partager la réponse

### Statistiques

- 📈 Panel affichant les statistiques des FAQs
- 🎯 Score moyen basé sur les feedbacks
- 📊 Nombre total de feedbacks par FAQ
- 🔄 Mise à jour en temps réel

## 🎨 Structure

```
advanced_chat/
├── index.html         # Structure HTML principale
├── main.js           # Logique JavaScript (chat + feedback)
├── styles.css        # Styles et animations
├── TESTING_FEEDBACK.md # Guide de test du feedback
└── start_server.py   # Serveur HTTP local
```

## � PWA indépendante

- Fichiers PWA isolés : `frontend/pwa/`
- Doc PWA dédiée : `frontend/pwa/doc/GUIDE_PWA.md`
- Accès rapide : `frontend/index.html` redirige ou pointe vers `frontend/pwa/index.html`

## �🚀 Utilisation

### Lancer le serveur frontend

```bash
python start_server.py
# L'interface est disponible sur http://localhost:8080
```

### Architecture API

| Endpoint            | Méthode | Description                                        |
| ------------------- | ------- | -------------------------------------------------- |
| `/api/chatbot/ask/` | POST    | Poser une question et obtenir les FAQs pertinentes |
| `/api/feedback/`    | POST    | Envoyer un feedback (positif/négatif)              |
| `/api/stats/`       | GET     | Récupérer les statistiques des FAQs                |

## 🔄 Intégration Backend

### Modèle de Feedback

Le système de feedback utilise le modèle `Feedback` du backend:

```python
{
    "faq": <id_faq>,
    "score_similarite": 0 ou 1,  # 1 = positif, 0 = négatif
    "comment": "Texte du feedback"
}
```

### Signaux (Bloc 2)

Chaque feedback déclenche automatiquement:

- Mise à jour de la `popularity`
- Ajustement du coefficient `norm`
- Réduction du `score_similarite` pour les feedbacks négatifs

📖 Voir `backend/CHANGELOG_BLOC2_SIGNALS.md` pour plus de détails.

## 🎯 Détection d'Endpoints

L'interface détecte automatiquement le backend selon le contexte:

```javascript
// Si sur ngrok frontend → utiliser ngrok backend
if (host.includes("ngrok-free.dev")) {
  return "https://patternable-felicitously-shaunta.ngrok-free.dev";
}

// Si sur réseau local (192.168.x.x) → utiliser l'IP locale
if (host.includes("192.168") || host.includes("10.")) {
  return `http://${host}:8000`;
}

// Sinon → localhost (développement local)
return "http://localhost:8000";
```

## 🎨 Personnalisation

### Couleurs

Les couleurs sont définies dans les variables CSS (`:root` de `styles.css`):

- **Primaire**: `#1a4594` (bleu SUP'PTIC)
- **Accent**: `#60a5fa` (bleu clair)
- **Succès**: `#10b981` (vert)
- **Avertissement**: `#f59e0b` (orange)

### Messages d'Accueil

Modifier le contenu de `.welcome-message` dans `index.html`:

```html
<div class="welcome-message">
  <div class="welcome-icon"><i class="bi bi-hand-thumbs-up"></i></div>
  <h2>Bienvenue sur l'Assistant SUP'PTIC</h2>
  <p>Posez vos questions sur la FAQ de l'établissement</p>
</div>
```

### Suggestions Initiales

Les suggestions peuvent être modifiées dans les `.suggestion-card`:

```html
<button class="suggestion-card" data-question="Votre question ici">
  <span class="suggestion-icon"><i class="bi bi-book"></i></span>
  <span class="suggestion-text">Label affiché</span>
</button>
```

## 🔧 Fichiers Clés

### `main.js` - Logique Principale

**Fonctions principales:**

- `ask(question, topK)` - Envoie une question à l'API
- `sendFeedback(faqId, isPositive)` - Envoie un feedback
- `loadStats()` - Charge les statistiques
- `toggleStatsPanel()` - Bascule le panel de stats
- `attachFeedbackListeners()` - Attache les event listeners au feedback

**Flux d'exécution:**

1. Utilisateur saisit une question
2. `ask()` envoie à `/api/chatbot/ask/`
3. Les résultats sont formatés et affichés
4. Les boutons de feedback deviennent cliquables
5. Clic sur 👍/👎 → `sendFeedback()` → API `/api/feedback/`
6. Toast de confirmation et boutons désactivés

### `styles.css` - Styling

**Classes principales:**

- `.chat-container` - Conteneur principal
- `.chat-header` - En-tête
- `.chat-body` - Zone de conversation
- `.bubble.bot / .bubble.user` - Messages
- `.result-item` - Une réponse FAQ
- `.feedback-btn` - Boutons de feedback
- `.stats-toggle / .stats-panel` - Statistiques

## 📱 Responsive

L'interface est responsive et s'adapte à:

- Desktop (1024px+)
- Tablette (576px+)
- Mobile (<576px)

Breakpoints:

- `@media (max-width: 576px)` - Mobile
- `@media (max-width: 380px)` - Petit mobile

## 🐛 Débogage

### Console du Navigateur

L'application log les informations utiles:

```javascript
console.log("✅ SUP'PTIC Assistant initialisé");
console.log("🔗 API:", API_URL);
```

Ouvrez la console (F12) pour voir:

- Les appels API
- Les erreurs de feedback
- Les statistiques chargées

### Network Tab

Vérifiez dans les outils de dev (F12 → Network):

- ✅ `POST /api/chatbot/ask/` - Succès 200
- ✅ `POST /api/feedback/` - Succès 201
- ✅ `GET /api/stats/` - Succès 200

## 📝 Changelog

### Dernières Modifications

**Intégration Feedback (v2.1)**

- ✅ Ajout des boutons de feedback (👍👎📋📤)
- ✅ Intégration API POST `/api/feedback/`
- ✅ Panel de statistiques en temps réel
- ✅ Détection automatique des endpoints
- ✅ Notifications toast de confirmation

## 🤝 Support

Pour les problèmes:

1. Consultez `TESTING_FEEDBACK.md`
2. Vérifiez `backend/CORS_CONFIGURATION.md`
3. Ouvrez la console (F12) pour les erreurs
