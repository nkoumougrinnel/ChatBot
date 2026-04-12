# 🧠 Documentation — `backend/chatbot/engine/`

> **Projet** : SUP'ONE — Assistant intelligent du Club Informatique de SUP'PTIC
> **Phase** : 2 — Pipeline RAG (Retrieval-Augmented Generation)
> **Stack** : MiniLM · FAISS · Ollama (Phi-3 Mini) · TF-IDF · Django

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture du module](#2-architecture-du-module)
3. [Dépendances](#3-dépendances)
4. [embedder.py](#4-embedderpy)
5. [faiss_search.py](#5-faiss_searchpy)
6. [llm_client.py](#6-llm_clientpy)
7. [prompt_builder.py](#7-prompt_builderpy)
8. [tfidf_fallback.py](#8-tfidf_fallbackpy)
9. [rag_pipeline.py](#9-rag_pipelinepy)
10. [Flux de données complet](#10-flux-de-données-complet)
11. [Seuils de confiance](#11-seuils-de-confiance)
12. [Tests rapides](#12-tests-rapides)

---

## 1. Vue d'ensemble

Le dossier `engine/` est le **cœur du système RAG**. Il orchestre toute la chaîne de traitement d'une question : de la vectorisation jusqu'à la génération de la réponse par le LLM local.

### Principe général

```
Question de l'étudiant
         │
         ▼
    embedder.py        →  Vecteur float32 (384 dim)
         │
         ▼
   faiss_search.py     →  Top-3 résultats (score cosinus)
         │
         ├── score ≥ 0.55 ──→  prompt_builder.py  →  llm_client.py  →  Réponse Phi-3
         │
         └── score < 0.55 ──→  tfidf_fallback.py  →  Réponse TF-IDF Phase 1
```

Tous les modules sont **indépendants et testables** directement avec `python fichier.py`.

---

## 2. Architecture du module

```
backend/chatbot/engine/
│
├── __init__.py           # Déclaration du package
├── embedder.py           # Vectorisation MiniLM (all-MiniLM-L6-v2)
├── faiss_search.py       # Index FAISS + recherche vectorielle
├── llm_client.py         # Client HTTP Ollama — Phi-3 Mini
├── prompt_builder.py     # Construction du prompt structuré Phi-3
├── rag_pipeline.py       # Orchestrateur principal (point d'entrée Django)
└── tfidf_fallback.py     # Fallback TF-IDF Phase 1
```

**Seul `rag_pipeline.py` doit être importé par les vues Django.** Les autres modules sont des composants internes appelés par le pipeline.

---

## 3. Dépendances

```bash
pip install sentence-transformers   # MiniLM
pip install faiss-cpu               # Index vectoriel
pip install scikit-learn            # TF-IDF fallback
```

Pour le LLM local (Ollama), aucune dépendance Python supplémentaire — le client utilise `urllib` de la bibliothèque standard.

```bash
# Installer et démarrer Ollama
ollama serve
ollama pull phi3:mini
```

---

## 4. `embedder.py`

### Rôle

Charge le modèle `all-MiniLM-L6-v2` **une seule fois** au démarrage (pattern singleton) et transforme n'importe quel texte en vecteur numérique normalisé de 384 dimensions.

### Fonctions

#### `encode(text) → np.ndarray`

Vectorise une phrase en un vecteur `(384,)` float32 normalisé.

```python
from chatbot.engine.embedder import encode
import numpy as np

v1 = encode("C'est combien pour s'inscrire ?")
v2 = encode("Quels sont les frais de scolarité ?")

# Vecteurs normalisés → dot product = similarité cosinus
similarity = float(np.dot(v1, v2))   # ~0.87 (synonymes sémantiques)
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `text` | `str` | Texte à vectoriser |
| **Retour** | `np.ndarray (384,) float32` | Vecteur normalisé |

---

#### `encode_batch(texts) → np.ndarray`

Vectorise une liste de textes en une seule passe GPU/CPU. Plus efficace qu'appeler `encode()` en boucle.

```python
from chatbot.engine.embedder import encode_batch

texts = ["Question 1", "Question 2", "Question 3"]
matrix = encode_batch(texts)   # shape: (3, 384)
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `texts` | `list[str]` | Liste de textes à vectoriser |
| **Retour** | `np.ndarray (N, 384) float32` | Matrice de vecteurs normalisés |

> **Note** : Utilisé par `build_index.py` pour vectoriser toute la base FAQ en une seule opération.

---

#### `get_dimension() → int`

Retourne `384` — la dimension des vecteurs produits par le modèle.

---

### Comportements importants

- Le modèle est chargé **une seule fois** en mémoire grâce au lazy singleton `_get_model()`. Les appels suivants sont instantanés.
- `normalize_embeddings=True` est activé : la norme de chaque vecteur vaut `1.0`, ce qui permet d'utiliser le **produit scalaire** comme équivalent de la similarité cosinus.
- Premier chargement : ~2–3 secondes (téléchargement du modèle ~90 Mo si absent).

---

## 5. `faiss_search.py`

### Rôle

Gère l'**index FAISS en mémoire**. Chargé au démarrage de Django via `AppConfig.ready()`. Permet de retrouver instantanément les k vecteurs les plus proches d'une question.

### Fichiers requis

| Fichier | Généré par | Description |
|---------|-----------|-------------|
| `rag_data/index.bin` | `build_index.py` | Index FAISS sérialisé |
| `rag_data/metadata.json` | `build_index.py` | Mapping `vecteur_id` ↔ réponse |

### Fonctions

#### `load_index(index_path, metadata_path) → None`

Charge l'index FAISS et les métadonnées depuis le disque. **Appelé automatiquement par `AppConfig.ready()`** au démarrage Django.

```python
import faiss_search
faiss_search.load_index()   # une seule fois au démarrage
```

---

#### `search(query_vec, k=3) → list[tuple[int, float]]`

Retourne les `k` résultats les plus proches sous forme brute.

```python
from chatbot.engine.embedder import encode
from chatbot.engine.faiss_search import search

vec = encode("frais de scolarité")
results = search(vec, k=3)
# [(42, 0.8731), (17, 0.8105), (93, 0.7642)]
# →  (metadata_id, score_cosinus)
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `query_vec` | `np.ndarray (384,) float32` | Vecteur de la question |
| `k` | `int` | Nombre de résultats (défaut : 3) |
| **Retour** | `list[tuple[int, float]]` | Liste de `(metadata_id, score)` |

---

#### `search_with_metadata(query_vec, k=3) → list[dict]`

Comme `search()` mais enrichi automatiquement des métadonnées. **C'est cette fonction qui est utilisée par `rag_pipeline.py`.**

```python
results = search_with_metadata(vec, k=3)
```

Chaque dict retourné contient :

```python
{
    "vecteur_id": 42,
    "score":      0.8731,          # similarité cosinus
    "response":   "Les frais s'élèvent à 500 000 FCFA...",
    "example":    "C'est combien pour s'inscrire ?",
    "categorie":  "Admissions",
    "source":     "e-supptic.cm",
    "intent":     "faq_admissions_001"
}
```

---

#### `reload_index() → None`

Recharge l'index **à chaud sans redémarrer Django**. Appelé par l'endpoint `POST /api/reload-index/` après une mise à jour de la base FAQ.

---

#### `get_index_stats() → dict`

```python
{
    "loaded":         True,
    "ntotal":         420,    # nombre de vecteurs dans l'index
    "dim":            384,
    "metadata_count": 420
}
```

---

#### `is_loaded() → bool`

Retourne `True` si l'index est chargé en mémoire.

---

### Type d'index FAISS utilisé

`IndexFlatIP` (Inner Product) — sur des vecteurs normalisés, le produit interne est équivalent à la similarité cosinus. La recherche est **exacte** (pas d'approximation).

---

## 6. `llm_client.py`

### Rôle

Client HTTP léger vers l'**API Ollama locale** (Phi-3 Mini). N'utilise que `urllib` (bibliothèque standard Python) — aucune dépendance externe.

### Configuration

| Variable d'environnement | Défaut | Description |
|--------------------------|--------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL du serveur Ollama |
| `OLLAMA_MODEL` | `phi3:mini` | Modèle à utiliser |

### Fonctions

#### `generate(prompt, model, **kwargs) → str`

Génération **bloquante** : attend la réponse complète avant de retourner.

```python
from chatbot.engine.llm_client import generate

reponse = generate(prompt)
print(reponse)   # Texte complet de la réponse
```

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `prompt` | `str` | — | Prompt complet formaté Phi-3 |
| `model` | `str` | `phi3:mini` | Modèle Ollama |
| `**kwargs` | — | — | Surcharge les paramètres de génération |
| **Retour** | `str` | — | Texte de la réponse |

---

#### `generate_stream(prompt, model, **kwargs) → Iterator[str]`

Génération en **streaming** : yield chaque token dès sa production. Utilisé pour les réponses progressives dans l'interface web.

```python
from chatbot.engine.llm_client import generate_stream

for token in generate_stream(prompt):
    print(token, end="", flush=True)
```

---

#### `check_availability(model) → dict`

Vérifie qu'Ollama est démarré et que le modèle est disponible.

```python
status = check_availability()
# {"available": True, "model": "phi3:mini", "error": None}
```

---

### Paramètres de génération par défaut

| Paramètre | Valeur | Raison |
|-----------|--------|--------|
| `temperature` | `0.3` | Réponses factuelles et déterministes |
| `num_predict` | `512` | Longueur max de la réponse |
| `top_p` | `0.9` | Nucleus sampling |
| `stop` | `["</s>", "[INST]"]` | Tokens d'arrêt du template Phi-3 |

Tous surchargeable à l'appel : `generate(prompt, temperature=0.7)`.

---

## 7. `prompt_builder.py`

### Rôle

Construit le prompt complet envoyé à Phi-3 en respectant son **template natif** `<|system|>...<|user|>...<|assistant|>`. Intègre l'historique de conversation et les contextes FAISS pour que le LLM génère une réponse précise et ancrée dans les données de SUP'PTIC.

### Fonctions

#### `build_prompt(question, contexts, history) → str`

Construit le prompt complet.

```python
from chatbot.engine.prompt_builder import build_prompt

contexts = [
    {
        "score":    0.91,
        "categorie": "Admissions",
        "source":   "e-supptic.cm",
        "response": "Les frais sont de 500 000 FCFA par an."
    }
]
history = [
    {"role": "user",      "content": "Quelles filières existent ?"},
    {"role": "assistant", "content": "Il y a Réseaux et Télécoms."}
]

prompt = build_prompt("Et les frais ?", contexts, history)
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `question` | `str` | Question de l'étudiant |
| `contexts` | `list[dict]` | Top-k résultats de `search_with_metadata()` |
| `history` | `list[dict]` \| `None` | Derniers échanges. Format : `[{"role": "user"\|"assistant", "content": "..."}]` |
| **Retour** | `str` | Prompt complet formaté pour Phi-3 |

> **Important** : L'historique est limité aux **3 derniers échanges** pour ne pas dépasser la fenêtre de contexte de Phi-3 Mini.

---

#### `build_no_context_prompt(question) → str`

Prompt de fallback quand FAISS ne retourne aucun résultat. Le LLM est contraint à indiquer qu'il ne peut pas répondre.

---

### Structure du prompt généré

```
<|system|>
Tu es SUP'ONE, l'assistant intelligent du Club Informatique de SUP'PTIC...
Tu réponds UNIQUEMENT en français.
Tu te bases EXCLUSIVEMENT sur les informations fournies dans le contexte.
<|end|>
<|user|>
[Historique de la conversation]
Étudiant : Quelles filières existent ?
Assistant : Il y a Réseaux et Télécoms.

[Informations disponibles sur SUP'PTIC]
--- Information 1 [Admissions | Source : e-supptic.cm] (pertinence : 0.91) ---
Les frais sont de 500 000 FCFA par an.

Question de l'étudiant : Et les frais ?
Réponds uniquement à partir des informations fournies ci-dessus.
<|end|>
<|assistant|>
```

---

### Contraintes du message système

Le LLM est hardcodé pour :
1. Répondre **uniquement en français**
2. Se baser **exclusivement** sur le contexte fourni (pas d'hallucination)
3. Retourner un message d'indirection standard si l'information est absente

---

## 8. `tfidf_fallback.py`

### Rôle

Encapsule le moteur **TF-IDF de la Phase 1** comme mécanisme de repli. Activé automatiquement par `rag_pipeline.py` quand le score FAISS est insuffisant (< 0.55). Garantit qu'une réponse cohérente est toujours retournée même pour les questions peu fréquentes.

### Fonctions

#### `load(data_dir, cache_path) → None`

Initialise le moteur TF-IDF. Charge depuis le cache pickle si disponible, sinon reconstruit depuis les fichiers JSON.

```python
import tfidf_fallback
tfidf_fallback.load()   # appelé une fois au démarrage
```

---

#### `search(query, top_k=1) → tuple[str, float, str]`

Retourne le meilleur résultat TF-IDF.

```python
answer, score, method = tfidf_fallback.search("tarif scolarité suptptic")
# ("Les frais s'élèvent à...", 0.6234, "TF-IDF")
```

| Retour | Type | Description |
|--------|------|-------------|
| `answer` | `str` | Texte de la réponse |
| `score` | `float` | Similarité cosinus TF-IDF (0.0 à 1.0) |
| `method` | `str` | Toujours `"TF-IDF"` |

---

#### `search_top_k(query, k=3) → list[dict]`

Top-k résultats avec métadonnées complètes. Chaque dict contient `answer`, `score`, `question`, `categorie`, `method`.

---

#### `rebuild(data_dir, cache_path) → None`

Force la reconstruction complète du cache TF-IDF (supprime l'ancien et recrée depuis les JSON).

---

#### `get_stats() → dict`

```python
{"loaded": True, "entries_count": 350, "vocab_size": 8420}
```

---

### Stratégie de cache

| Étape | Action |
|-------|--------|
| Premier lancement | Lit les JSON → construit le vectoriseur → sérialise dans `tfidf_cache.pkl` |
| Lancements suivants | Charge directement `tfidf_cache.pkl` (~10× plus rapide) |
| Après mise à jour FAQ | Appeler `rebuild()` pour régénérer le cache |

---

### Paramètres du vectoriseur TF-IDF

| Paramètre | Valeur | Rôle |
|-----------|--------|------|
| `ngram_range` | `(1, 2)` | Unigrammes et bigrammes |
| `max_features` | `20 000` | Taille maximale du vocabulaire |
| `sublinear_tf` | `True` | Atténue les mots très fréquents (`log(tf)`) |

---

## 9. `rag_pipeline.py`

### Rôle

**Point d'entrée unique du module `engine/`.** Orchestre tous les autres composants. C'est le seul fichier que les vues Django importent.

### Fonctions

#### `ask(question, history) → dict`

Réponse **complète et bloquante**.

```python
from chatbot.engine.rag_pipeline import ask

result = ask(
    question="C'est combien pour s'inscrire ?",
    history=[
        {"role": "user",      "content": "Bonjour"},
        {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"}
    ]
)
```

**Retour :**

```python
{
    "answer":     "Les frais de scolarité à SUP'PTIC s'élèvent à 500 000 FCFA...",
    "sources": [
        {
            "question":  "C'est combien pour s'inscrire ?",
            "score":     0.8731,
            "categorie": "Admissions",
            "source":    "e-supptic.cm"
        }
    ],
    "method":     "RAG",      # "RAG" ou "TF-IDF"
    "best_score": 0.8731
}
```

---

#### `ask_stream(question, history) → Iterator[str | dict]`

Réponse en **streaming SSE**. Yield trois types d'événements dans l'ordre :

| Ordre | Type | Contenu |
|-------|------|---------|
| 1 | `dict` | `{"type": "meta", "method": "RAG", "sources": [...], "best_score": 0.87, "low_confidence": false}` |
| 2…N | `str` | Fragments de texte du LLM (tokens) |
| Dernier | `dict` | `{"type": "done"}` |

---

#### `build_sse_event(data) → str`

Formate un événement pour `StreamingHttpResponse` de Django.

```python
# str → {"type": "token", "content": "Les frais..."}
# dict → {"type": "meta", ...} ou {"type": "done"}
```

---

### Intégration dans une vue Django

```python
from django.http import StreamingHttpResponse
from chatbot.engine.rag_pipeline import ask_stream, build_sse_event

def chat_stream_view(request):
    question = request.GET.get("q", "")
    history  = request.session.get("history", [])

    def event_stream():
        for chunk in ask_stream(question, history):
            yield build_sse_event(chunk)

    return StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream"
    )
```

---

## 10. Flux de données complet

```
┌─────────────────────────────────────────────────────────────┐
│                      Vue Django                             │
│          ask(question, history)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │  embedder.py   │  encode(question)  →  vec (384,) float32
          └────────┬───────┘
                   │
                   ▼
         ┌──────────────────┐
         │ faiss_search.py  │  search_with_metadata(vec, k=3)
         └────────┬─────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
  score ≥ 0.55           score < 0.30
       │                     │
       ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│prompt_builder│    │ tfidf_fallback   │
│    .py       │    │      .py         │
└──────┬───────┘    └────────┬─────────┘
       │                     │
       ▼                     │
┌──────────────┐             │
│ llm_client   │             │
│    .py       │             │
└──────┬───────┘             │
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
         ┌────────────────┐
         │  rag_pipeline  │  {"answer", "sources", "method", "best_score"}
         └────────────────┘
```

---

## 11. Seuils de confiance

| Seuil | Variable d'env. | Défaut | Comportement |
|-------|----------------|--------|--------------|
| `SCORE_HIGH` | `RAG_SCORE_HIGH` | `0.55` | Score FAISS ≥ 0.55 → RAG complet |
| `SCORE_MED` | `RAG_SCORE_MED` | `0.30` | Score FAISS ∈ [0.30, 0.55[ → RAG + ⚠️ avertissement |
| — | — | < 0.30 | Score FAISS < 0.30 → bascule TF-IDF |

Le message d'avertissement affiché en mode `RAG_LOW` :

```
⚠️ Cette réponse est approximative — la pertinence est modérée.
Vérifiez auprès du secrétariat si nécessaire.
```

---

## 12. Tests rapides

Chaque module peut être testé indépendamment :

```bash
# Tester la vectorisation MiniLM
python backend/chatbot/engine/embedder.py

# Tester la recherche FAISS (nécessite index.bin)
python backend/chatbot/engine/faiss_search.py

# Tester le client Ollama (nécessite ollama serve)
python backend/chatbot/engine/llm_client.py

# Tester la construction du prompt
python backend/chatbot/engine/prompt_builder.py

# Tester le fallback TF-IDF (nécessite data/*.json)
python backend/chatbot/engine/tfidf_fallback.py

# Tester le pipeline complet
python backend/chatbot/engine/rag_pipeline.py
```

Via Django :

```bash
python manage.py test chatbot.tests.test_embedder
python manage.py test chatbot.tests.test_faiss_search
python manage.py test chatbot.tests.test_fallback
```

---

*Documentation des fichiers backend pour le projet SUP'ONE Phase 2 — Club Informatique SUP'PTIC — 2025/2026*
