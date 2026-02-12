# Architecture du Cœur du ChatBot

## Vue d'ensemble

L'application chatbot est organisée autour de trois modules spécialisés, organisés en pipeline :

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHAÎNE DE TRAITEMENT                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  preprocessing.py    │  → TextPreprocessor (classe)
│                      │  → preprocess_text() fonction
│  Dépendances:        │     (singleton lazy avec spaCy)
│  - spacy             │
└──────────────────────┘
          ▲
          │ importe preprocess_text
          │
┌──────────────────────┐
│ vectorization.py     │  → train_vectorizer()
│                      │  → compute_tfidf_vector()
│ Dépendances:         │  → compute_and_store_vectors()
│ - preprocessing      │
│   (preprocess_text)  │  Utilise:
│ - sklearn            │  • preprocess_text() avant fit/transform
│ - faq.models         │  • FAQ, FAQVector (Django)
│ - numpy              │
└──────────────────────┘
          ▲
          │ importe compute_tfidf_vector
          │
┌──────────────────────┐
│  similarity.py       │  → compute_cosine_similarity()
│                      │  → find_best_faq()
│ Dépendances:         │
│ - vectorization      │  Utilise:
│   (compute_tfidf_    │  • compute_tfidf_vector() pour
│    vector)           │    vectoriser la question user
│ - faq.models         │  • FAQVector.tfidf_vector (BD)
│ - numpy              │  • Calcul cosinus (produit scalaire/norme)
└──────────────────────┘
          ▲
          │ importe
          │ (compute_cosine_similarity,
          │  find_best_faq)
          │
┌──────────────────────┐
│    utils.py          │  Point d'entrée UNIQUE
│                      │  (réexporte tout)
│ Dépendances:         │
│ - preprocessing      │  Exporte:
│ - vectorization      │  • preprocess_text
│ - similarity         │  • TextPreprocessor
│                      │  • train_vectorizer
└──────────────────────┘  • compute_tfidf_vector
                          • compute_and_store_vectors
                          • compute_cosine_similarity
                          • find_best_faq
```

## Tableau des imports

| Module             | Importe depuis                         | Utilise pour                          |
| ------------------ | -------------------------------------- | ------------------------------------- |
| `preprocessing.py` | spacy                                  | Charger modèle FR, tokenize/lemmatize |
| `vectorization.py` | `preprocessing.preprocess_text()`      | Prétraiter avant entraîner TF-IDF     |
| `vectorization.py` | sklearn, numpy, faq.models             | Vectoriser, stocker en BD             |
| `similarity.py`    | `vectorization.compute_tfidf_vector()` | Vectoriser la question user           |
| `similarity.py`    | numpy, faq.models                      | Calcul similarité, requête BD         |
| `utils.py`         | tous les 3 modules                     | Centraliser l'API publique            |

## Flux d'exécution (exemple)

```
Question utilisateur: "Je veux réinitialiser mon mot de passe"
         ↓
  find_best_faq() [similarity.py]
         ↓
    ├─→ compute_tfidf_vector() [vectorization.py]
    │       ├─→ preprocess_text() [preprocessing.py]
    │       │       └─→ spaCy model chargé une fois (singleton)
    │       │           Résultat: ["vouloir", "réinitialiser", "mot_passe"]
    │       │
    │       └─→ TF-IDF transform sur tokens
    │           Résultat: vecteur numpy 1D + norme L2
    │
    ├─→ Récupère FAQVector.tfidf_vector depuis la BD
    │       (vecteurs pré-calculés pour chaque FAQ)
    │
    └─→ compute_cosine_similarity()
            Calcul: dot_product / (norm1 × norm2)
            Résultat: score ∈ [0, 1]

Résultat final: liste des top_k FAQs avec scores
```

## Détails par module

### 1. `preprocessing.py` - Prétraitement du texte

**Classe:** `TextPreprocessor`

- Initialise spaCy avec modèle français (`fr_core_news_sm`)
- Applique: tokenization → lemmatization → suppression stopwords → filtre alphabétique

**Fonction:** `preprocess_text(text: str) -> List[str]`

- Interface publique
- Utilise singleton lazy pour éviter de recharger spaCy à chaque appel

**Optimisation:**

- Singleton lazy via `get_preprocessor()`
- Le modèle spaCy n'est chargé qu'une seule fois en mémoire

### 2. `vectorization.py` - Vectorisation TF-IDF

**Fonction:** `train_vectorizer(corpus)`

- Entraîne `TfidfVectorizer` sur un corpus de textes prétraités
- Stocke le vectorizer en variable globale

**Fonction:** `compute_tfidf_vector(text: str) -> (np.ndarray, float)`

- Retourne tuple: (vecteur TF-IDF, norme L2)
- Applique `preprocess_text()` avant transformation
- Norme utile pour normalisation en BD et calcul cosinus optimisé

**Fonction:** `compute_and_store_vectors()`

- Boucle sur toutes les FAQ en base
- Calcule et persiste vecteurs TF-IDF + norme dans `FAQVector`

### 3. `similarity.py` - Calcul de similarité

**Fonction:** `compute_cosine_similarity(vec1, vec2) -> float`

- Calcul direct: `dot(v1, v2) / (norm(v1) × norm(v2))`
- Plus rapide que sklearn (pas de reshape)
- Gère cas zero-norm, clip score ∈ [0, 1]

**Fonction:** `find_best_faq(question: str, top_k: int = 3) -> list[dict]`

- Pipeline complet:
  1. Vectorise la question (appelle `compute_tfidf_vector`)
  2. Récupère tous les `FAQVector` de la BD
  3. Calcule similarité cosinus vs chaque FAQ
  4. Retourne top_k par score décroissant
- Chaque résultat: `{'faq': FAQ_object, 'score': float ∈ [0, 1]}`

### 4. `utils.py` - Point d'entrée unique

Réexporte toutes les fonctions publiques:

```python
__all__ = [
    'preprocess_text',
    'TextPreprocessor',
    'train_vectorizer',
    'compute_tfidf_vector',
    'compute_and_store_vectors',
    'compute_cosine_similarity',
    'find_best_faq',
]
```

**Usage:**

```python
from chatbot.utils import find_best_faq

results = find_best_faq("Mes question", top_k=3)
for r in results:
    print(r['score'], r['faq'].question)
```

## Dépendances externes

- **spacy** : NLP français (modèle `fr_core_news_sm`)
- **scikit-learn** : `TfidfVectorizer`
- **numpy** : calculs vectoriels
- **Django** : modèles ORM (`FAQ`, `FAQVector`, `Category`, `Feedback`)

## Tests

Exécutez le script de test complet :

```bash
python scripts/test_chatbot_core.py
```

Teste les 4 étapes:

1. Prétraitement (tokenization/lemmatization)
2. Vectorisation (TF-IDF)
3. Similarité (calculs cosinus)
4. Pipeline end-to-end (création FAQs → vectorisation → recherche)
