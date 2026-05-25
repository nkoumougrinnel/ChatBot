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
8. [rag_pipeline.py](#8-rag_pipelinepy)
9. [Flux de données complet](#9-flux-de-données-complet)
10. [Seuils de confiance](#10-seuils-de-confiance)
11. [Tests rapides](#11-tests-rapides)

---

## 1. Vue d'ensemble

Le dossier `engine/` est le **cœur du système RAG**. Il orchestre toute la chaîne de traitement d'une question : de la vectorisation jusqu'à la génération de la réponse par le LLM local.

### Principe général

```
Question de l'étudiant
        │
        ▼
    [Niveau 1] _detect_conversational → Réponse immédiate (salut, merci, etc.)
        │
        ▼
    [Sinon]
        │
        ▼
    embedder.py        →  Vecteur float32 (384 dim)
        │
        ▼
   faiss_search.py     →  Top-1 résultat (score cosinus)
        │
        ├── score ≥ 0.55 ──→  prompt_builder.py  →  llm_client.py  →  Réponse DIRECT (base FAQ)
        └── score < 0.55 ──→  prompt_builder.py  →  llm_client.py  →  Réponse fallback LLM (pas de contexte)
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
└── rag_pipeline.py       # Orchestrateur principal (pipeline 3 niveaux)
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

````bash
# Installer et démarrer Ollama
ollama serve
ollama pull phi3:mini

## 8. `rag_pipeline.py`

### Rôle

**Point d'entrée unique du module `engine/`.** Orchestration du pipeline RAG à 3 niveaux :

1. **Niveau 1 — CONV** : détection et réponse immédiate aux questions conversationnelles (salutations, remerciements, etc.)
2. **Niveau 2 — DIRECT** : si le score FAISS ≥ 0.55, réponse directe depuis la base FAQ (contexte fourni au LLM)
3. **Niveau 3 — LLM** : si le score FAISS < 0.55, génération fallback par le LLM (prompt sans contexte, réponse standard ou d'indisponibilité)

### Fonctions principales

- `ask(question, history) → dict` : réponse complète et bloquante (voir ci-dessous)
- `ask_stream(question, history) → Iterator[str | dict]` : réponse en streaming SSE (voir ci-dessous)
- `build_sse_event(data) → str` : formatte un événement SSE pour Django

#### Exemple d'appel

```python
from chatbot.engine.rag_pipeline import ask

result = ask(
    question="C'est combien pour s'inscrire ?",
    history=[
        {"role": "user",      "content": "Bonjour"},
        {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"}
    ]
)
````

**Retour :**

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
    "method":     "DIRECT",      # "CONV", "DIRECT" ou "LLM"
    "best_score": 0.8731
}
```

#### Streaming SSE

`ask_stream` yield trois types d'événements dans l'ordre :

| Ordre   | Type   | Contenu                                                    |
| ------- | ------ | ---------------------------------------------------------- |
| 1       | `dict` | `{"type": "meta", "method": "DIRECT", "score": 0.87, ...}` |
| 2…N     | `str`  | Fragments de texte du LLM (tokens)                         |
| Dernier | `dict` | `{"type": "done"}`                                         |

#### Intégration Django

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

| Paramètre   | Type                        | Description                      |
| ----------- | --------------------------- | -------------------------------- |
| `query_vec` | `np.ndarray (384,) float32` | Vecteur de la question           |
| `k`         | `int`                       | Nombre de résultats (défaut : 3) |
| **Retour**  | `list[tuple[int, float]]`   | Liste de `(metadata_id, score)`  |

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

| Variable d'environnement | Défaut                   | Description           |
| ------------------------ | ------------------------ | --------------------- |
| `OLLAMA_BASE_URL`        | `http://localhost:11434` | URL du serveur Ollama |
| `OLLAMA_MODEL`           | `phi3:mini`              | Modèle à utiliser     |

### Fonctions

#### `generate(prompt, model, **kwargs) → str`

Génération **bloquante** : attend la réponse complète avant de retourner.

```python
from chatbot.engine.llm_client import generate

reponse = generate(prompt)
print(reponse)   # Texte complet de la réponse
```

| Paramètre  | Type  | Défaut      | Description                            |
| ---------- | ----- | ----------- | -------------------------------------- |
| `prompt`   | `str` | —           | Prompt complet formaté Phi-3           |
| `model`    | `str` | `phi3:mini` | Modèle Ollama                          |
| `**kwargs` | —     | —           | Surcharge les paramètres de génération |
| **Retour** | `str` | —           | Texte de la réponse                    |

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

| Paramètre     | Valeur               | Raison                               |
| ------------- | -------------------- | ------------------------------------ |
| `temperature` | `0.3`                | Réponses factuelles et déterministes |
| `num_predict` | `512`                | Longueur max de la réponse           |
| `top_p`       | `0.9`                | Nucleus sampling                     |
| `stop`        | `["</s>", "[INST]"]` | Tokens d'arrêt du template Phi-3     |

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

| Paramètre  | Type                   | Description                                                                     |
| ---------- | ---------------------- | ------------------------------------------------------------------------------- |
| `question` | `str`                  | Question de l'étudiant                                                          |
| `contexts` | `list[dict]`           | Top-k résultats de `search_with_metadata()`                                     |
| `history`  | `list[dict]` \| `None` | Derniers échanges. Format : `[{"role": "user"\|"assistant", "content": "..."}]` |
| **Retour** | `str`                  | Prompt complet formaté pour Phi-3                                               |

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

| Ordre   | Type   | Contenu                                                                                            |
| ------- | ------ | -------------------------------------------------------------------------------------------------- |
| 1       | `dict` | `{"type": "meta", "method": "RAG", "sources": [...], "best_score": 0.87, "low_confidence": false}` |
| 2…N     | `str`  | Fragments de texte du LLM (tokens)                                                                 |
| Dernier | `dict` | `{"type": "done"}`                                                                                 |

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
     ┌──────────────────────────────┐
     │ _detect_conversational()     │
     └─────────────┬────────────────┘
             │
     ┌─────────────┴─────────────┐
     │                           │
   [match CONV]                [sinon]
     │                           │
     ▼                           ▼
   Réponse CONV  ┌────────────────┐
                 │  embedder.py   │  encode(question)
                 └────────┬───────┘
                    │
                    ▼
                ┌──────────────────┐
                │ faiss_search.py  │  search_with_metadata(vec, k=1)
                └────────┬─────────┘
                      │
              ┌─────────────┴─────────────┐
              │                           │
        score ≥ 0.55                  score < 0.55
              │                           │
              ▼                           ▼
        ┌────────────────┐          ┌──────────────────────┐
        │prompt_builder  │          │prompt_builder        │
        │+ llm_client    │          │+ llm_client          │
        │(contexte FAQ)  │          │(prompt fallback)     │
        └──────┬─────────┘          └──────────┬───────────┘
            │                              │
            ▼                              ▼
        ┌────────────────┐             ┌───────────────┐
        │  rag_pipeline  │             │ rag_pipeline  │
        └────────────────┘             └───────────────┘
```

---

## 11. Seuils de confiance

| Seuil          | Variable d'env.  | Défaut | Comportement                                                            |
| -------------- | ---------------- | ------ | ----------------------------------------------------------------------- |
| `SCORE_DIRECT` | `RAG_SCORE_HIGH` | `0.55` | Score FAISS ≥ 0.55 → méthode DIRECT (réponse FAQ)                       |
| —              | —                | < 0.55 | Score FAISS < 0.55 → méthode LLM (génération fallback, pas de contexte) |

Résumé :

- **CONV** : détection conversationnelle → réponse immédiate
- **DIRECT** : score FAISS ≥ 0.55 → réponse FAQ
- **LLM** : score FAISS < 0.55 → génération fallback (réponse standard ou d'indisponibilité)

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

_Documentation des fichiers backend pour le projet SUP'ONE Phase 2 — Club Informatique SUP'PTIC — 2025/2026_
