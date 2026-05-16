# FLUX_RAG.md — Pipeline RAG de SUP'ONE Phase 2

> **Projet** : ChatBot SUP'ONE — Club Informatique SUP'PTIC  
> **Version** : 2.0.0  
> **Date** : Avril 2026

---

## Vue d'ensemble

Le pipeline RAG (Retrieval-Augmented Generation) est le cœur du système SUP'ONE Phase 2. Il transforme une question brute en réponse naturelle en combinant recherche vectorielle et génération par LLM local.

```
Question de l'étudiant
        │
        ▼
   1. EMBEDDING        →  Vecteur float32 (384 dim)        [embedder.py]
        │
        ▼
   2. RECHERCHE FAISS  →  Top-3 résultats (score cosinus)  [faiss_search.py]
        │
        ▼
   3. ÉVALUATION DU SCORE
        │
        ├── score ≥ 0.55  →  4a. CONSTRUCTION PROMPT       [prompt_builder.py]
        │                         │
        │                         ▼
        │                    4b. GÉNÉRATION LLM             [llm_client.py]
        │                         │
        │                         ▼
        │                    5. RÉPONSE RAG
        │
        └── score < 0.55  →  4c. FALLBACK TF-IDF           [tfidf_fallback.py]
                                  │
                                  ▼
                             5. RÉPONSE TF-IDF
```

---

## Étape 1 — Embedding (embedder.py)

### Rôle

Transformer la question texte en vecteur numérique que FAISS peut comparer.

### Modèle utilisé

`all-MiniLM-L6-v2` de HuggingFace — modèle léger (90 Mo) optimisé pour la similarité sémantique.

### Fonctionnement

```python
from chatbot.engine.embedder import encode

vec = encode("C'est combien pour s'inscrire ?")
# → np.ndarray shape=(384,) dtype=float32 norme=1.0
```

### Propriétés du vecteur produit

| Propriété | Valeur |
|---|---|
| Dimension | 384 |
| Type | float32 |
| Norme | 1.0 (normalisé) |
| Temps de calcul | < 50 ms après warmup |

### Pourquoi MiniLM plutôt que TF-IDF

TF-IDF compare des mots exacts. MiniLM comprend le **sens** :

```
TF-IDF : "frais scol" ≠ "tarif inscription"  (0 mots en commun)
MiniLM : "frais scol" ≈ "tarif inscription"  (similarité ~0.85)
```

---

## Étape 2 — Recherche FAISS (faiss_search.py)

### Rôle

Trouver instantanément les k entrées de la base les plus proches sémantiquement de la question.

### Type d'index

`IndexFlatIP` (Inner Product) — sur des vecteurs normalisés, le produit interne est équivalent à la similarité cosinus. Recherche **exacte** (pas d'approximation).

### Fonctionnement

```python
from chatbot.engine.faiss_search import search_with_metadata

results = search_with_metadata(vec, k=3)
# → [
#     {"score": 0.87, "response": "Les frais...", "categorie": "Admissions"},
#     {"score": 0.72, "response": "Le paiement...", "categorie": "Admissions"},
#     {"score": 0.61, "response": "Pour les boursiers...", "categorie": "Admissions"},
#   ]
```

### Fichiers requis

| Fichier | Généré par | Contenu |
|---|---|---|
| `rag_data/index.bin` | `build_index.py` | Vecteurs sérialisés |
| `rag_data/metadata.json` | `build_index.py` | Mapping vecteur_id ↔ réponse |

### Chargement au démarrage

L'index est chargé **une seule fois** en mémoire via `AppConfig.ready()` au démarrage Django. Les appels suivants sont instantanés.

---

## Étape 3 — Évaluation du score

### Seuils de décision

| Zone | Condition | Comportement |
|---|---|---|
| RAG | score ≥ 0.55 | LLM appelé, réponse de qualité |
| RAG_LOW | score ∈ [0.50, 0.55[ | LLM appelé + avertissement ⚠ |
| TF-IDF | score < 0.50 | LLM non appelé, réponse Phase 1 |

### Variables d'environnement

```bash
RAG_SCORE_HIGH=0.55   # seuil RAG
RAG_SCORE_MED=0.50    # seuil RAG_LOW
RAG_TOP_K=3           # nombre de résultats FAISS
```

---

## Étape 4a — Construction du prompt (prompt_builder.py)

### Rôle

Assembler un prompt structuré pour Phi-3 Mini qui inclut le contexte FAISS, l'historique de conversation et la question.

### Format Phi-3

```
<|system|>
Tu es SUP'ONE, l'assistant du Club Informatique de SUP'PTIC.
Tu réponds UNIQUEMENT en français.
Tu te bases EXCLUSIVEMENT sur le contexte fourni.
<|end|>
<|user|>
[Historique de la conversation]        ← 3 derniers échanges max
Étudiant : ...
Assistant : ...

[Informations disponibles sur SUP'PTIC]
--- Information 1 [Admissions] (pertinence : 0.87) ---
Les frais s'élèvent à 525 000 FCFA...

Question de l'étudiant : C'est combien pour s'inscrire ?
<|end|>
<|assistant|>
```

### Contraintes du LLM

- Répond **uniquement en français**
- Se base **exclusivement** sur le contexte fourni
- Indique explicitement s'il ne trouve pas l'information (pas d'hallucination)

---

## Étape 4b — Génération LLM (llm_client.py)

### Rôle

Envoyer le prompt à Ollama (Phi-3 Mini) et récupérer la réponse générée.

### Paramètres de génération

| Paramètre | Valeur | Rôle |
|---|---|---|
| `temperature` | 0.3 | Réponses factuelles et déterministes |
| `num_predict` | 150 | Longueur max de la réponse |
| `num_ctx` | 512 | Fenêtre de contexte |
| `num_thread` | 4 | Threads CPU utilisés |

### Mode streaming

```python
for token in generate_stream(prompt):
    yield token   # chaque mot envoyé immédiatement au Frontend
```

### Timeout

```bash
RAG_LLM_TIMEOUT=60   # secondes avant abandon
```

---

## Étape 4c — Fallback TF-IDF (tfidf_fallback.py)

### Activation

Automatique quand le score FAISS < 0.50. Le LLM n'est **pas** appelé.

### Avantage

Réponse **immédiate** (< 1 seconde) sans risque de timeout.

### Seuil interne TF-IDF

Si la similarité TF-IDF < 0.05 → message d'indirection :
```
"Je n'ai pas trouvé d'information correspondant à votre question.
Contactez le secrétariat de SUP'PTIC pour plus de détails."
```

---

## Étape 5 — Streaming SSE vers le Frontend

### Format des événements

```
data: {"type": "meta",  "method": "RAG", "best_score": 0.87, "sources": [...]}\n\n
data: {"type": "token", "content": "Les "}\n\n
data: {"type": "token", "content": "frais "}\n\n
data: {"type": "token", "content": "s'élèvent à..."}\n\n
data: {"type": "done"}\n\n
```

### Headers Django

```python
response["Content-Type"]       = "text/event-stream"
response["Cache-Control"]      = "no-cache"
response["X-Accel-Buffering"]  = "no"   # désactive buffer Nginx
```

---

## Métriques de performance cibles

| Indicateur | Objectif | Mesuré sur |
|---|---|---|
| Latence embedding | < 50 ms | Une phrase |
| Latence FAISS | < 5 ms | Index de 1000 vecteurs |
| Latence LLM | < 40 s | EliteBook 840 G3 (CPU) |
| Taux RAG (score ≥ 0.55) | > 60% | 50 questions variées |
| Tests unitaires | 100% passants | `python manage.py test` |

---

*Document produit par l'équipe Backend — Club Informatique SUP'PTIC — Phase 2 — Avril 2026*
