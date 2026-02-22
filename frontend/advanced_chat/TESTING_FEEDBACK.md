# Guide de Test - Fonctionnalité Feedback

## 📋 Résumé des Modifications

L'index HTML de advanced_chat a été enrichi avec les éléments suivants pour tester la fonctionnalité de feedback implémentée en backend:

### 1. **Boutons de Feedback sur chaque réponse**

- **👍 Like** - Envoyer un feedback positif (score_similarite = 1)
- **👎 Dislike** - Envoyer un feedback négatif (score_similarite = 0)
- **📋 Copy** - Copier la réponse
- **📤 Share** - Partager la réponse

### 2. **Panel de Statistiques**

- **Bouton "📊 Statistiques"** - Affiche un panel avec les statistiques des FAQs
- **Tableau des FAQs** - Affiche le score moyen et le nombre de feedbacks par FAQ
- Mise à jour en temps réel des scores

### 3. **Notifications Toast**

- Confirmation visuelle lors de l'envoi d'un feedback
- Messages d'erreur en cas de problème

## 🚀 Comment Tester

### Étape 1: Démarrer le serveur backend

```bash
cd backend
python manage.py runserver 8000
```

### Étape 2: Servir le frontend

```bash
cd frontend/advanced_chat
python start_server.py
# Ou avec un serveur HTTP local
# python -m http.server 8080
```

### Étape 3: Ouvrir le chatbot

```
http://localhost:8080 (ou le port utilisé)
```

### Étape 4: Tester les Feedbacks

1. **Poser une question** (ex: "Quelle est l'histoire de SUP'PTIC ?")
2. **Attendre la réponse** - Les boutons de feedback apparaissent
3. **Cliquer sur 👍 ou 👎** - Un toast de confirmation s'affiche
4. **Boutons désactivés** - Une fois cliqué, les boutons changent de couleur

### Étape 5: Vérifier les Statistiques

1. **Cliquer sur "📊 Statistiques"** en bas à droite
2. **Voir le panel** avec:
   - Nom de la FAQ
   - Score moyen (basé sur les feedbacks)
   - Nombre de feedbacks

## 📊 Impact du Feedback sur les Scores

D'après le CHANGELOG_BLOC2_SIGNALS.md, voici ce qui se passe:

### Feedback Positif (👍):

- `popularity += 1`
- `norm *= 1.1` (augmente jusqu'à 1.0 max)
- Score inchangé

### Feedback Négatif (👎):

- `popularity -= 1` (min 0)
- `norm *= 0.9` (diminue jusqu'à 0.1 min)
- `score_similarite *= 0.7` (réduit de 30%)

## 🔗 Endpoints API Utilisés

### 1. Poser une Question

```
POST /api/chatbot/ask/
Body: {"question": "...", "top_k": 3}
```

### 2. Envoyer un Feedback

```
POST /api/feedback/
Body: {
  "faq": <faq_id>,
  "score_similarite": 0 ou 1,
  "comment": "Feedback text"
}
```

### 3. Récupérer les Statistiques

```
GET /api/stats/
Response: [
  {
    "id": 1,
    "question": "...",
    "avg_score": 0.85,
    "count": 5
  }
]
```

## 🎯 Scénario de Test Complet

1. Poser 3 questions différentes
2. Pour chaque réponse:
   - Donner un feedback positif à certaines
   - Donner un feedback négatif à d'autres
3. Ouvrir le panel de statistiques
4. Vérifier que:
   - Les scores moyens se mettent à jour
   - Les compteurs de feedbacks augmentent
   - Les FAQs mal notées ont un score bas

## 📝 Notes Importantes

- Les feedbacks sont **enregistrés avec un utilisateur anonyme** si pas authentifié
- Les feedbacks **persistent en base de données**
- Les **signaux** (signals.py) mettent automatiquement à jour les scores
- Le **cache** de 1 heure peut être vidé à `/admin/` si nécessaire

## 🛠️ Fichiers Modifiés

1. `frontend/advanced_chat/index.html` - Ajout du panel de statistiques
2. `frontend/advanced_chat/styles.css` - Styles pour les boutons et le panel
3. `frontend/advanced_chat/main.js` - Logique de feedback et statistiques

## 🐛 Dépannage

**Q: Les boutons de feedback ne répondent pas?**

- Vérifiez que `main.js` est bien chargé
- Ouvrez la console (F12) pour les erreurs

**Q: Les statistiques ne se mettent pas à jour?**

- Actualisez manuellement le panel
- Vérifiez que l'API `/api/stats/` répond

**Q: L'erreur CORS apparaît?**

- Vérifiez la configuration CORS en `backend/CORS_CONFIGURATION.md`
- Assurez-vous que ngrok ou l'IP locale est correctement configurée
