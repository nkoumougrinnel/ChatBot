# OLLAMA_SETUP.md — Guide d'installation et configuration d'Ollama

> **Projet** : ChatBot SUP'ONE — Club Informatique SUP'PTIC  
> **Version** : 2.0.0  
> **Date** : Avril 2026

---

## Qu'est-ce qu'Ollama

Ollama est un serveur local qui fait tourner des LLM (Large Language Models) directement sur ta machine, sans connexion internet et sans coût d'API. SUP'ONE utilise **Phi-3 Mini** via Ollama pour générer les réponses naturelles du chatbot.

---

## 1. Installation

### Windows

```powershell
# Télécharger l'installeur depuis https://ollama.com/download
# Puis exécuter OllamaSetup.exe

# Vérifier l'installation
ollama --version
```

### Linux / Mac

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

---

## 2. Démarrer le serveur

Ollama doit tourner en arrière-plan avant de lancer Django.

```powershell
# Ouvrir un terminal séparé et lancer
ollama serve
```

Le serveur écoute sur `http://localhost:11434`.

Vérifier qu'il répond :

```powershell
curl http://localhost:11434/api/tags
```

Réponse attendue :
```json
{"models": [...]}
```

---

## 3. Télécharger le modèle Phi-3 Mini

**À faire une seule fois avec internet.**

```powershell
ollama pull phi3:mini
```

Téléchargement : ~2.4 Go — à faire **avant la démo**, pas le jour J.

Vérifier que le modèle est disponible :

```powershell
ollama list
```

Résultat attendu :
```
NAME            ID              SIZE    MODIFIED
phi3:mini       ...             2.4 GB  ...
```

---

## 4. Tester le modèle

```powershell
ollama run phi3:mini "Bonjour, réponds en une phrase en français."
```

Réponse attendue en moins de 40 secondes :
```
Bonjour ! Je suis SUP'ONE, l'assistant de SUP'PTIC.
```

---

## 5. Paramètres utilisés par SUP'ONE

Ces paramètres sont configurés dans `backend/chatbot/engine/llm_client.py` :

| Paramètre | Valeur | Explication |
|---|---|---|
| `temperature` | `0.3` | Réponses factuelles, peu créatives |
| `num_predict` | `150` | Longueur maximale de la réponse |
| `num_ctx` | `512` | Taille de la fenêtre de contexte |
| `num_thread` | `4` | Threads CPU (adapté EliteBook 840 G3) |
| `top_p` | `0.9` | Nucleus sampling |
| `stop` | `["</s>", "[INST]"]` | Tokens d'arrêt Phi-3 |

---

## 6. Variables d'environnement

```bash
OLLAMA_BASE_URL=http://localhost:11434   # URL du serveur Ollama
OLLAMA_MODEL=phi3:mini                   # Modèle à utiliser
RAG_LLM_TIMEOUT=60                       # Timeout en secondes
```

Sur Windows PowerShell :

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL    = "phi3:mini"
$env:RAG_LLM_TIMEOUT = "60"
```

---

## 7. Optimisations pour machines sans GPU

Le HP EliteBook 840 G3 n'a pas de GPU dédié. Appliquer ces optimisations avant de lancer Ollama :

### Brancher le chargeur
Windows bride le CPU sur batterie. **Toujours brancher le chargeur** avant de lancer Ollama.

### Activer le mode Haute Performance

```powershell
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
```

### Fermer les applications gourmandes

```powershell
# Voir ce qui consomme la RAM
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name, @{N='RAM_Mo';E={[math]::Round($_.WorkingSet/1MB,1)}}
```

Fermer : Chrome (onglets inutiles), Teams, OneDrive, antivirus si possible.

### Temps de réponse attendu après optimisation

| Configuration | Temps moyen |
|---|---|
| Sans optimisation, batterie | > 120s (timeout) |
| Avec optimisation, branché | 25 à 40s |
| Avec GPU dédié | 3 à 8s |

---

## 8. Mode hors ligne (obligatoire après installation)

Une fois le modèle téléchargé, Ollama fonctionne **entièrement hors ligne**. Pour éviter que HuggingFace vérifie les mises à jour au démarrage, ajouter dans `settings.py` :

```python
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"]  = "1"
```

---

## 9. Résolution des problèmes fréquents

### Ollama ne répond pas

```powershell
# Vérifier que le serveur tourne
curl http://localhost:11434/api/tags

# Si rien → relancer
ollama serve
```

### TimeoutError dans Django

```
TimeoutError: timed out
```

Causes possibles :

| Cause | Solution |
|---|---|
| Machine sur batterie | Brancher le chargeur |
| Trop d'apps ouvertes | Fermer Chrome, Teams |
| Modèle trop lourd | Utiliser `phi3:mini-q4_K_M` |
| Timeout trop court | `$env:RAG_LLM_TIMEOUT = "120"` |

### Modèle phi3:mini absent

```powershell
ollama pull phi3:mini
```

### Vérification complète en une commande

```powershell
& c:/Users/HP/Desktop/ChatBot/.venv/Scripts/python.exe -c "
import urllib.request, json
try:
    r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
    data = json.loads(r.read())
    models = [m['name'] for m in data.get('models', [])]
    print('Ollama OK — modeles :', models)
    if not any('phi3' in m for m in models):
        print('ATTENTION : phi3:mini absent — lancez : ollama pull phi3:mini')
except Exception as e:
    print('Ollama inaccessible :', e)
"
```

---

## 10. Procédure de démarrage complète (ordre à respecter)

```
1. Brancher le chargeur
2. Activer mode Haute Performance
3. Fermer les apps inutiles
4. Terminal 1 → ollama serve
5. Vérifier : curl http://localhost:11434/api/tags
6. Terminal 2 → python manage.py runserver
7. Tester : Thunder Client → POST /api/chatbot/ask/
```

---

*Document produit par l'équipe Backend — Club Informatique SUP'PTIC — Phase 2 — Avril 2026*
