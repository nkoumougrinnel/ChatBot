# Schéma Phase 2 — Base de données

## Objectif

Documenter le modèle de données Phase 1 et identifier les extensions nécessaires pour la Phase 2 RAG.

## Audit des modèles Phase 1

### `Category`

- `name`: `models.CharField(max_length=100, unique=True)`
- `description`: `models.TextField(blank=True)`
- `active`: `models.BooleanField(default=True)`

### Observation — Category

- Le modèle `Category` est suffisant pour la classification des FAQ.
- Aucun champ RAG spécifique n'est requis ici.

### `FAQ`

- `question`: `models.TextField()`
- `answer`: `models.TextField()`
- `category`: `models.ForeignKey(Category, on_delete=models.RESTRICT)`
- `subtheme`: `models.CharField(max_length=100, blank=True)`
- `source`: `models.CharField(max_length=200, blank=True)`
- `created_at`: `models.DateTimeField(auto_now_add=True)`
- `updated_at`: `models.DateTimeField(auto_now=True)`
- `is_active`: `models.BooleanField(default=True)`
- `popularity`: `models.IntegerField(default=0)`

### Observation — FAQ

- Le champ `source` est déjà présent et correspond bien à la provenance de la réponse.
- Lier une FAQ à une position dans l'index FAISS (`embedding_id`) n'est pas recommandé : cette position dépend de l'ordre d'ajout des vecteurs dans `index.bin` et change à chaque rebuild.
- Il peut être utile de tracer la méthode de recherche ici lorsqu'une FAQ est liée à des réponses de pipeline, mais ce champ est plutôt métier/transactionnel.

### `FAQVector`

- `faq`: `models.OneToOneField(FAQ, on_delete=models.CASCADE, related_name='vector')`
- `tfidf_vector`: `models.JSONField()`
- `norm`: `models.FloatField()`
- `computed_at`: `models.DateTimeField(auto_now_add=True)`

### Observation — FAQVector

- `FAQVector` stocke les vecteurs TF-IDF Phase 1.
- Pour la Phase 2, la liaison entre FAQ et FAISS doit rester gérée par `metadata.json` plutôt que par un champ `embedding_id` en base.

### `Feedback`

- `user`: `models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
- `faq`: `models.ForeignKey(FAQ, on_delete=models.CASCADE)`
- `feedback_type`: `models.CharField(max_length=20, choices=[('positif', 'Positif'), ('negatif', 'Négatif')])`
- `question_utilisateur`: `models.TextField()`
- `comment`: `models.TextField(blank=True)`
- `score_similarite`: `models.FloatField(null=True, blank=True)`
- `created_at`: `models.DateTimeField(auto_now_add=True)`

### Observation — Feedback

- Le modèle `Feedback` est correctement dimensionné pour Phase 1.
- Pour tracer l'origine de la réponse en Phase 2, il manque un champ :
  - `rag_method`: `models.CharField(max_length=10, choices=[('RAG', 'RAG'), ('TF-IDF', 'TF-IDF')], default='TF-IDF')`

## Schéma ER actualisé

### `Category` — Updated Schema

- `id`: `AutoField` (clé primaire)
- `name`: `CharField(max_length=100, unique=True)`
- `description`: `TextField(blank=True)`
- `active`: `BooleanField(default=True)`

### `FAQ` — Updated Schema

- `id`: `AutoField`
- `question`: `TextField()`
- `answer`: `TextField()`
- `category_id`: `ForeignKey(Category, on_delete=models.RESTRICT)`
- `subtheme`: `CharField(max_length=100, blank=True)`
- `source`: `CharField(max_length=200, blank=True)`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `updated_at`: `DateTimeField(auto_now=True)`
- `is_active`: `BooleanField(default=True)`
- `popularity`: `IntegerField(default=0)`

### `FAQVector` - Updated Schema

- `id`: `AutoField`
- `faq_id`: `OneToOneField(FAQ, on_delete=models.CASCADE, related_name='vector')`
- `tfidf_vector`: `JSONField()`
- `norm`: `FloatField()`
- `computed_at`: `DateTimeField(auto_now_add=True)`

### `Feedback` - Updated Schema

- `id`: `AutoField`
- `user_id`: `ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
- `faq_id`: `ForeignKey(FAQ, on_delete=models.CASCADE)`
- `feedback_type`: `CharField(max_length=20, choices=[('positif', 'Positif'), ('negatif', 'Négatif')])`
- `question_utilisateur`: `TextField()`
- `comment`: `TextField(blank=True)`
- `score_similarite`: `FloatField(null=True, blank=True)`
- `rag_method`: `CharField(max_length=10, choices=[('RAG', 'RAG'), ('TF-IDF', 'TF-IDF')], default='TF-IDF')`
- `created_at`: `DateTimeField(auto_now_add=True)`
