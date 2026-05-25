# Implémentation API REST - Documentation Technique

Document technique détaillant l'implémentation complète de l'API REST du chatbot avec Django REST Framework.

---

## Vue d'ensemble

L'API REST expose le pipeline chatbot via des endpoints HTTP standardisés. Les clients peuvent :

- **Lister** les FAQs et catégories
- **Créer** des FAQs et catégories (authentifiés)
- **Poser des questions** et obtenir les réponses pertinentes (public)
- **Envoyer des feedbacks** sur les réponses (public)

---

## Architecture des couches

```
┌─────────────────────────────────────────────────────────┐
│          CLIENTS (curl, Postman, Web Frontend)          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP Requests
                     ↓
┌─────────────────────────────────────────────────────────┐
│             Django URL Router (urls.py)                 │
│  Mappe /api/categories/ → CategoryViewSet, etc.         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│             Views (ViewSets) - views.py                 │
│  Handle requests, validation, permissions, responses    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│          Serializers - serializers.py                   │
│  Convert request JSON ↔ Django models                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Django Models (faq.models)                      │
│  Category, FAQ, FAQVector, Feedback                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Chatbot Pipeline (chatbot.utils, vectorization, etc.)  │
│  find_best_faq() → retourne FAQs pertinentes            │
└─────────────────────────────────────────────────────────┘
```

---

## Fichiers créés/modifiés

### 1. `backend/faq/serializers.py` (NEW)

**Rôle :** Définir les schémas de sérialisation/désérialisation JSON ↔ modèles Django

**Serializers créés :**

```python
class CategorySerializer(ModelSerializer)
    # Sérialise les catégories FAQ
    # Champs: id, name, description, active

class FAQSerializer(ModelSerializer)
    # Sérialise les FAQs complètement
    # Inclut: id, question, answer, category (nested), vector (nested)
    # Accepte category_id en écriture

class FAQListSerializer(ModelSerializer)
    # Version légère pour lister FAQs (sans vecteur)
    # Champs: id, question, category_name, subtheme, is_active, popularity

class FAQVectorSerializer(ModelSerializer)
    # Vecteurs TF-IDF (lecture seule)
    # Champs: id, norm, computed_at

class FeedbackSerializer(ModelSerializer)
    # Feedbacks utilisateurs
    # Champs: id, user, faq, feedback_type, question_utilisateur, etc.

class QuestionRequestSerializer(Serializer)
    # Validation requête POST /api/chatbot/ask/
    # Champs: question (str), top_k (int, défaut 3)

class ChatbotResponseSerializer(Serializer)
    # Format réponse du chatbot
    # Retourne: question, results (liste FAQs + scores), count
```

**Points clés :**

- Relations nested (Category dans FAQ)
- Champs write_only (category_id) et read_only (timestamps)
- Validation personnalisée (top_k entre 1 et 10)

---

### 2. `backend/faq/views.py` (MODIFIED)

**Rôle :** Implémenter la logique métier des endpoints

**ViewSets créés :**

```python
class CategoryViewSet(ModelViewSet)
    # Endpoints: GET/POST /api/categories/
    # Lectures : publiques (AllowAny)
    # Modifications : authentifiées (IsAuthenticated)

class FAQViewSet(ModelViewSet)
    # Endpoints: GET/POST /api/faq/
    # Retourne FAQListSerializer pour list(), FAQSerializer pour detail()
    # Filtrage : is_active=True uniquement

class ChatbotAskViewSet(ViewSet)
    # Endpoint: POST /api/chatbot/ask/
    # CŒUR DU CHATBOT
    # 1. Valide la requête (QuestionRequestSerializer)
    # 2. Appelle find_best_faq(question, top_k)
    # 3. Formate les résultats (ChatbotResponseSerializer)
    # 4. Gère les erreurs (Vectorizer not trained, etc.)

class FeedbackViewSet(ModelViewSet)
    # Endpoints: POST /api/feedback/
    # POST : publique (permet feedbacks anonymes)
    # GET : authentifiée (admin seul)
    # Définit user=request.user automatiquement
```

**Permissions :**

- Lectures : `AllowAny` (public)
- Créations/Modifications : `IsAuthenticated` (protégées)
- Chatbot ask : `AllowAny` (public)
- Feedback POST : `AllowAny` (public)

---

### 3. `backend/faq/urls.py` (NEW)

**Rôle :** Enregistrer les ViewSets via DRF Router

```python
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faq', FAQViewSet, basename='faq')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'chatbot', ChatbotAskViewSet, basename='chatbot')

# Génère automatiquement :
# GET    /api/categories/
# POST   /api/categories/
# GET    /api/categories/{id}/
# PUT    /api/categories/{id}/
# DELETE /api/categories/{id}/
# (et similaires pour faq, feedback, chatbot)
```

---

### 4. `backend/config/urls.py` (MODIFIED)

**Modification :** Inclure les URLs de l'app `faq`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('faq.urls')),  # ← AJOUTÉ
]
```

Cela mount tous les endpoints sous `/api/` prefix.

---

### 5. `backend/faq/apps.py` (MODIFIED)

**Modification :** Initialiser le vectorizer au démarrage de Django

```python
class FaqConfig(AppConfig):
    name = 'faq'

    def ready(self):
        """Entraîner le vectorizer TF-IDF au démarrage."""
        try:
            from chatbot.vectorization import compute_and_store_vectors
            print("[FAQ] Initialisation du vectorizer TF-IDF...")
            compute_and_store_vectors()
            print("[FAQ] ✓ Vectorizer entraîné")
        except Exception as e:
            print(f"[FAQ] ⚠ Erreur : {e}")
```

**Pourquoi :** Le vectorizer est une variable globale en mémoire. Sans cette initialisation, il n'existait que dans le process du Django shell, pas dans le serveur API.

---

## Flux des requêtes

### Exemple : POST /api/chatbot/ask/

```
1. CLIENT envoie :
   POST /api/chatbot/ask/
   {
     "question": "Je veux réinitialiser mon mot de passe",
     "top_k": 3
   }

2. Django URL ROUTER
   Mappe à ChatbotAskViewSet.ask() action

3. SERIALIZER validation (QuestionRequestSerializer)
   ✓ Vérifie question (max 1000 chars)
   ✓ Vérifie top_k (1-10)

4. VIEW logique
   user_vec, user_norm = compute_tfidf_vector(question)
       ↓ appelle preprocessing.preprocess_text()
       ↓ applique TF-IDF transform

   faq_results = find_best_faq(question, top_k)
       ↓ boucle sur FAQVector en BD
       ↓ calcule similarité cosinus
       ↓ trie par score décroissant

5. FORMAT résultats (ChatbotResponseSerializer)
   {
     "question": "...",
     "results": [
       {
         "faq_id": 1,
         "question": "Comment réinitialiser mon mot de passe ?",
         "answer": "...",
         "score": 0.9503,
         "category": "Support"
       },
       ...
     ],
     "count": 1
   }

6. CLIENT reçoit réponse JSON 200 OK
```

---

## Endpoints complets

| Méthode   | Endpoint                | Authentification | Rôle                     |
| --------- | ----------------------- | ---------------- | ------------------------ |
| GET       | `/api/categories/`      | Public           | Lister catégories        |
| POST      | `/api/categories/`      | ✓ Protégé        | Créer catégorie          |
| GET       | `/api/categories/{id}/` | Public           | Détail catégorie         |
| PUT/PATCH | `/api/categories/{id}/` | ✓ Protégé        | Modifier catégorie       |
| DELETE    | `/api/categories/{id}/` | ✓ Protégé        | Supprimer catégorie      |
| GET       | `/api/faq/`             | Public           | Lister FAQs              |
| POST      | `/api/faq/`             | ✓ Protégé        | Créer FAQ                |
| GET       | `/api/faq/{id}/`        | Public           | Détail FAQ               |
| PUT/PATCH | `/api/faq/{id}/`        | ✓ Protégé        | Modifier FAQ             |
| DELETE    | `/api/faq/{id}/`        | ✓ Protégé        | Supprimer FAQ            |
| **POST**  | **`/api/chatbot/ask/`** | **Public**       | **⭐ Poser question**    |
| GET       | `/api/feedback/`        | ✓ Protégé        | Lister feedbacks (admin) |
| POST      | `/api/feedback/`        | Public           | Envoyer feedback         |

---

## Exemple d'utilisation complet

### 1. Démarrer le serveur

```powershell
python backend/manage.py runserver
```

Logs au démarrage :

```
[FAQ] Initialisation du vectorizer TF-IDF...
[FAQ] ✓ Vectorizer entraîné et FAQVectors stockés en BD
...
Starting development server at http://127.0.0.1:8000/
```

### 2. Poser une question

```powershell
curl -X POST http://localhost:8000/api/chatbot/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"Je veux réinitialiser mon mot de passe\",\"top_k\":3}"
```

### 3. Recevoir la réponse

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
    }
  ],
  "count": 1
}
```

---

## Gestion des erreurs

### Cas 1 : Vectorizer not trained

**Cause :** `compute_and_store_vectors()` n'a pas été appelé

**Solution :** Redémarrer le serveur (appelle `apps.ready()`)

```
Réponse : 500 Internal Server Error
{"error":"Erreur lors de la recherche : Vectorizer not trained"}
```

### Cas 2 : Validation échouée

**Cause :** `question` manquant ou `top_k` invalide

**Réponse :** 400 Bad Request

```json
{
  "question": ["This field is required."],
  "top_k": ["Ensure this value is less than or equal to 10."]
}
```

### Cas 3 : Authentification requise

**Cause :** Tentative de POST /api/faq/ sans token

**Réponse :** 403 Forbidden

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Bonnes pratiques implémentées

✅ **Séparation des concerns**

- Serializers : validation et transformation
- Views : logique métier
- URLs : routing

✅ **Permissions granulaires**

- Lectures publiques (GET)
- Modifications authentifiées (POST/PUT/DELETE)

✅ **Nesting intelligent**

- Serializers imbriqués (Category dans FAQ)
- Relations optimisées (prefetch_related)

✅ **Gestion des erreurs**

- Try/catch dans views
- Messages d'erreur explicites
- Status codes HTTP appropriés

✅ **Performance**

- Vectorizer singleton lazy (chargé une fois)
- Prefetch relations DB
- Pagination possible (via DRF)

---

## Améliorations futures

1. **Authentification JWT** : Remplacer Token par JWT (plus sécurisé)
2. **Rate limiting** : Limiter requêtes par IP/utilisateur
3. **Caching** : Cache les résultats FAQ populaires
4. **Pagination** : Ajouter pagination pour les listes longues
5. **Filtering/Searching** : Filtrer FAQs par catégorie, date, etc.
6. **Analytics** : Tracker requêtes populaires, scores moyens
7. **Documentation Swagger** : Générer doc auto avec `drf-spectacular`

---

## Fichiers de référence

- [API_TEST_GUIDE.md](API_TEST_GUIDE.md) — Exemples curl PowerShell
- [ARCHITECTURE.md](ARCHITECTURE.md) — Architecture du pipeline chatbot
- [TEST_PIPELINE.md](TEST_PIPELINE.md) — Résultats tests en Django shell
