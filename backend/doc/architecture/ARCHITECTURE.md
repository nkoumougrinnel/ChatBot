# Architecture du CÅ“ur du ChatBot

## Vue d'ensemble

L'application chatbot est organisée autour de trois modules spécialisés, organisés en pipeline :

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    CHAàŽNE DE TRAITEMENT                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  preprocessing.py    â”‚  â†’ TextPreprocessor (classe)
â”‚                      â”‚  â†’ preprocess_text() fonction
â”‚  Dépendances:        â”‚     (singleton lazy avec spaCy)
â”‚  - spacy             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
          â–²
          â”‚ importe preprocess_text
          â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ vectorization.py     â”‚  â†’ train_vectorizer()
â”‚                      â”‚  â†’ compute_tfidf_vector()
â”‚ Dépendances:         â”‚  â†’ compute_and_store_vectors()
â”‚ - preprocessing      â”‚
â”‚   (preprocess_text)  â”‚  Utilise:
â”‚ - sklearn            â”‚  â€¢ preprocess_text() avant fit/transform
â”‚ - faq.models         â”‚  â€¢ FAQ, FAQVector (Django)
â”‚ - numpy              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
          â–²
          â”‚ importe compute_tfidf_vector
          â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  similarity.py       â”‚  â†’ compute_cosine_similarity()
â”‚                      â”‚  â†’ find_best_faq()
â”‚ Dépendances:         â”‚
â”‚ - vectorization      â”‚  Utilise:
â”‚   (compute_tfidf_    â”‚  â€¢ compute_tfidf_vector() pour
â”‚    vector)           â”‚    vectoriser la question user
â”‚ - faq.models         â”‚  â€¢ FAQVector.tfidf_vector (BD)
â”‚ - numpy              â”‚  â€¢ Calcul cosinus (produit scalaire/norme)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
          â–²
          â”‚ importe
          â”‚ (compute_cosine_similarity,
          â”‚  find_best_faq)
          â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚    utils.py          â”‚  Point d'entrée UNIQUE
â”‚                      â”‚  (réexporte tout)
â”‚ Dépendances:         â”‚
â”‚ - preprocessing      â”‚  Exporte:
â”‚ - vectorization      â”‚  â€¢ preprocess_text
â”‚ - similarity         â”‚  â€¢ TextPreprocessor
â”‚                      â”‚  â€¢ train_vectorizer
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â€¢ compute_tfidf_vector
                          â€¢ compute_and_store_vectors
                          â€¢ compute_cosine_similarity
                          â€¢ find_best_faq
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
         â†“
  find_best_faq() [similarity.py]
         â†“
    â”œâ”€â†’ compute_tfidf_vector() [vectorization.py]
    â”‚       â”œâ”€â†’ preprocess_text() [preprocessing.py]
    â”‚       â”‚       â””â”€â†’ spaCy model chargé une fois (singleton)
    â”‚       â”‚           Résultat: ["vouloir", "réinitialiser", "mot_passe"]
    â”‚       â”‚
    â”‚       â””â”€â†’ TF-IDF transform sur tokens
    â”‚           Résultat: vecteur numpy 1D + norme L2
    â”‚
    â”œâ”€â†’ Récupère FAQVector.tfidf_vector depuis la BD
    â”‚       (vecteurs pré-calculés pour chaque FAQ)
    â”‚
    â””â”€â†’ compute_cosine_similarity()
            Calcul: dot_product / (norm1 à— norm2)
            Résultat: score âˆˆ [0, 1]

Résultat final: liste des top_k FAQs avec scores
```

## Détails par module

### 1. `preprocessing.py` - Prétraitement du texte

**Classe:** `TextPreprocessor`

- Initialise spaCy avec modèle français (`fr_core_news_sm`)
- Applique: tokenization â†’ lemmatization â†’ suppression stopwords â†’ filtre alphabétique

**Fonction:** `preprocess_text(text: str) -> List[str]`

- Interface publique
- Utilise singleton lazy pour éviter de recharger spaCy à  chaque appel

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

- Calcul direct: `dot(v1, v2) / (norm(v1) à— norm(v2))`
- Plus rapide que sklearn (pas de reshape)
- Gère cas zero-norm, clip score âˆˆ [0, 1]

**Fonction:** `find_best_faq(question: str, top_k: int = 3) -> list[dict]`

- Pipeline complet:
  1. Vectorise la question (appelle `compute_tfidf_vector`)
  2. Récupère tous les `FAQVector` de la BD
  3. Calcule similarité cosinus vs chaque FAQ
  4. Retourne top_k par score décroissant
- Chaque résultat: `{'faq': FAQ_object, 'score': float âˆˆ [0, 1]}`

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
4. Pipeline end-to-end (création FAQs â†’ vectorisation â†’ recherche)

