# Bloc 1: API Feedback - Support des utilisateurs anonymes

## Modifications

### `backend/faq/views.py`

- Ajout de `django.core.cache` import
- Modification de `FeedbackViewSet.perform_create()`:
  - Crée automatiquement un utilisateur `anonymous` pour les feedbacks non authentifiés
  - Les utilisateurs authentifiés sont assignés correctement
  - Permet les feedbacks 100% publics sans authentification

### `backend/faq/serializers.py`

- Ajustement du `FeedbackSerializer`:
  - `user_username` marqué comme `required=False`
  - Permet la création de feedbacks sans user_id préalablement défini

## Endpoint

```
POST /api/feedback/
{
  "faq": 1,
  "feedback_type": "positif",
  "question_utilisateur": "...",
  "comment": "...",
  "score_similarite": 0.85
}
```

Résultat: **HTTP 201** - Feedback créé avec user='anonymous'

## Impact

✓ N'importe quel utilisateur peut envoyer un feedback sans s'authentifier
✓ Collecte maximale de données utilisateurs
✓ Utilisateur anonyme créé automatiquement si inexistant
