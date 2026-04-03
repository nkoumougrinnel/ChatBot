# Guide de Test des Endpoints API

Tester les endpoints REST du chatbot avec **curl** ou **Postman**.

## Démarrer le serveur

```powershell
cd C:\Users\DELL\Desktop\ChatBot
.venv\Scripts\Activate.ps1
python backend/manage.py runserver
```

Serveur accessible sur : `http://localhost:8000/`

---

## 1. GET /api/categories/ - Lister les catégories

### Avec PowerShell

```powershell
curl -X GET http://localhost:8000/api/categories/ ^
  -H "Content-Type: application/json"
```

### Résultat attendu

```json
[
  {
    "id": 1,
    "name": "Support",
    "description": "Questions de support technique",
    "active": true
  }
]
```

---

## 2. POST /api/categories/ - Créer une catégorie

**Nécessite authentification** (token JWT ou authentification session)

### Avec PowerShell

```powershell
curl -X POST http://localhost:8000/api/categories/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Token YOUR_AUTH_TOKEN" ^
  -d "{\"name\":\"Facturation\",\"description\":\"Questions sur les factures et paiements\",\"active\":true}"
```

### Résultat attendu

```json
{
  "id": 2,
  "name": "Facturation",
  "description": "Questions sur les factures et paiements",
  "active": true
}
```

---

## 3. GET /api/faq/ - Lister les FAQs

### Avec PowerShell

```powershell
curl -X GET http://localhost:8000/api/faq/ ^
  -H "Content-Type: application/json"
```

### Résultat attendu

```json
[
  {
    "id": 1,
    "question": "Comment réinitialiser mon mot de passe ?",
    "category_name": "Support",
    "subtheme": "",
    "is_active": true,
    "popularity": 0
  },
  {
    "id": 2,
    "question": "Quelle est votre politique de confidentialité ?",
    "category_name": "Support",
    "subtheme": "",
    "is_active": true,
    "popularity": 0
  }
]
```

---

## 4. GET /api/faq/{id}/ - Détail d'une FAQ

### Avec PowerShell

```powershell
curl -X GET http://localhost:8000/api/faq/1/ ^
  -H "Content-Type: application/json"
```

### Résultat attendu

```json
{
  "id": 1,
  "question": "Comment réinitialiser mon mot de passe ?",
  "answer": "Cliquez sur 'Mot de passe oublié' puis suivez les étapes par email.",
  "category": {
    "id": 1,
    "name": "Support",
    "description": "Questions de support technique",
    "active": true
  },
  "category_id": 1,
  "subtheme": "",
  "source": "",
  "created_at": "2026-02-09T10:30:00Z",
  "updated_at": "2026-02-09T10:30:00Z",
  "is_active": true,
  "popularity": 0,
  "vector": {
    "id": 1,
    "norm": 1.0,
    "computed_at": "2026-02-09T10:35:00Z"
  }
}
```

---

## 5. POST /api/chatbot/ask/ - Poser une question

**Endpoint principal du chatbot** - retourne les FAQs les plus pertinentes

### Avec PowerShell

```powershell
curl -X POST http://localhost:8000/api/chatbot/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"Je veux réinitialiser mon mot de passe\",\"top_k\":3}"
```

### Résultat attendu

```json
{
  "question": "Je veux réinitialiser mon mot de passe",
  "results": [
    {
      "faq_id": 1,
      "question": "Comment réinitialiser mon mot de passe ?",
      "answer": "Cliquez sur 'Mot de passe oublié' puis suivez les étapes par email.",
      "score": 0.9503,
      "category": "Support"
    },
    {
      "faq_id": 4,
      "question": "Comment contacter le support ?",
      "answer": "Envoyez un email à support@example.com ou appelez +33 1 23 45 67 89.",
      "score": 0.1414,
      "category": "Support"
    }
  ],
  "count": 2
}
```

### Test avec différentes questions

```powershell
# Question 2: RGPD
curl -X POST http://localhost:8000/api/chatbot/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"Parlez-moi de votre RGPD\",\"top_k\":2}"

# Question 3: Hors sujet
curl -X POST http://localhost:8000/api/chatbot/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"Coucou ça va ?\",\"top_k\":3}"
```

---

## 6. POST /api/faq/ - Créer une FAQ

**Nécessite authentification**

### Avec PowerShell

```powershell
curl -X POST http://localhost:8000/api/faq/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Token YOUR_AUTH_TOKEN" ^
  -d "{\"question\":\"Comment changer mon email ?\",\"answer\":\"Allez dans les paramètres du compte et cliquez sur Modifier Email.\",\"category_id\":1,\"subtheme\":\"Compte\",\"source\":\"FAQ interne\",\"is_active\":true}"
```

### Résultat attendu

```json
{
  "id": 5,
  "question": "Comment changer mon email ?",
  "answer": "Allez dans les paramètres du compte et cliquez sur Modifier Email.",
  "category": {...},
  "category_id": 1,
  "subtheme": "Compte",
  "source": "FAQ interne",
  "created_at": "2026-02-09T12:00:00Z",
  "updated_at": "2026-02-09T12:00:00Z",
  "is_active": true,
  "popularity": 0,
  "vector": null
}
```

**Note:** Après création, il faut appeler `compute_and_store_vectors()` dans Django shell pour vectoriser la nouvelle FAQ.

---

## 7. POST /api/feedback/ - Envoyer un feedback

Permet aux utilisateurs de noter la pertinence d'une réponse

### Avec PowerShell

```powershell
curl -X POST http://localhost:8000/api/feedback/ ^
  -H "Content-Type: application/json" ^
  -d "{\"faq\":1,\"feedback_type\":\"positif\",\"question_utilisateur\":\"Je veux réinitialiser mon mot de passe\",\"comment\":\"La réponse était très utile et complète.\",\"score_similarite\":0.9503}"
```

### Résultat attendu

```json
{
  "id": 1,
  "user": null,
  "user_username": null,
  "faq": 1,
  "faq_question": "Comment réinitialiser mon mot de passe ?",
  "feedback_type": "positif",
  "question_utilisateur": "Je veux réinitialiser mon mot de passe",
  "comment": "La réponse était très utile et complète.",
  "score_similarite": 0.9503,
  "created_at": "2026-02-09T12:05:00Z"
}
```

---

## Tester avec Postman

### Importer la collection

Créer une nouvelle request pour chaque endpoint :

1. **GET Categories**
   - Method: GET
   - URL: `http://localhost:8000/api/categories/`

2. **POST Ask**
   - Method: POST
   - URL: `http://localhost:8000/api/chatbot/ask/`
   - Body (raw JSON):
     ```json
     {
       "question": "Je veux réinitialiser mon mot de passe",
       "top_k": 3
     }
     ```

3. **GET FAQs**
   - Method: GET
   - URL: `http://localhost:8000/api/faq/`

---

## Authentification (Token)

Pour les endpoints protégés, obtenir un token :

### 1. Créer un utilisateur (admin)

```bash
python backend/manage.py createsuperuser
```

### 2. Obtenir le token (si DRF Token Auth configuré)

```powershell
curl -X POST http://localhost:8000/api-token-auth/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"YOUR_PASSWORD\"}"
```

Résultat:

```json
{
  "token": "1234567890abcdef1234567890abcdef"
}
```

### 3. Utiliser le token dans les requêtes

```powershell
curl -X POST http://localhost:8000/api/faq/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Token 1234567890abcdef1234567890abcdef" ^
  -d "{...}"
```

---

## Dépannage

### Erreur 404: Endpoint not found

- Vérifier que `faq/urls.py` est bien inclus dans `config/urls.py`
- Redémarrer le serveur Django

### Erreur 403: Permission Denied

- L'endpoint est protégé (authentification requise)
- Ajouter le header `Authorization: Token YOUR_TOKEN`

### Erreur 500: Internal Server Error

- Vérifier les logs Django
- Vérifier que `compute_and_store_vectors()` a été exécuté
- Vérifier que le modèle spaCy `fr_core_news_sm` est installé

### Vecteurs non trouvés

Le chatbot retourne une erreur si les FAQVectors ne sont pas calculées.
Exécuter dans le Django shell :

```python
from chatbot.utils import compute_and_store_vectors
compute_and_store_vectors()
```

---

## Points clés

✅ Endpoints publics : GET (lecture)  
✅ Endpoints protégés : POST/PUT/DELETE (modifications)  
✅ Endpoint chatbot : public (pas d'authentification)  
✅ Feedback : public (permet retours anonymes)  
✅ Scores de similarité : entre 0 et 1
