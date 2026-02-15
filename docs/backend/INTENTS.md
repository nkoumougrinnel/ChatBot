

---

# 📘 Documentation des Modifications Appliquées au Chatbot

## 1. Ajout de la Détection d’Intents

**Fichier concerné :** `intent_detection.py`
**Fonction ajoutée :** `detect_intent`

### Description

Cette fonction permet d’identifier l’intention (*intent*) d’une question posée par l’utilisateur à l’aide d’un modèle de classification supervisée.

### Paramètres d’entrée

* `question` *(str)* : question formulée par l’utilisateur
* `model` : modèle de classification entraîné (ex. *Logistic Regression*)
* `intents` *(list)* : liste des intents, contenant pour chacun :

  * des exemples de questions
  * des réponses associées

### Valeurs de sortie

* `intent` *(str)* : intent détecté
* `confidence` *(float)* : score de confiance de la prédiction
* `response` *(str)* : réponse associée à l’intent

### Gestion du cas d’échec (fallback)

Si aucun intent n’est détecté avec une confiance suffisante, la fonction retourne la réponse générique suivante :

> *« Désolé, je ne comprends pas votre question. »*

### Exemple d’utilisation

```python
intent, confidence, response = detect_intent(
    "Quels sont les horaires de la bibliothèque ?",
    model,
    intents
)
```

---

## 2. Entraînement du Modèle de Classification d’Intents

**Fichier concerné :** `train_intents.py`
**Fonction ajoutée :** `train_intent_classifier`

### Description

Cette fonction entraîne un modèle de classification d’intents à partir d’exemples de questions, en combinant :

* une vectorisation TF-IDF
* un classifieur *Logistic Regression*

### Paramètre d’entrée

* `intents` *(list)* : liste d’intents contenant des exemples de questions

### Sortie

* Un modèle entraîné capable de prédire l’intent associé à une question utilisateur

### Exemple d’utilisation

```python
from train_intents import train_intent_classifier

model = train_intent_classifier(intents)
```

---

## 3. Chargement des Intents

**Fichier concerné :** `intents_loader.py`
**Fonction ajoutée :** `load_intents`

### Description

Cette fonction charge les intents depuis un fichier JSON externe afin de séparer les données d’entraînement de la logique applicative.

### Paramètre d’entrée

* `file_path` *(str)* : chemin du fichier JSON contenant les intents

### Sortie

* Une liste structurée d’intents (intent, exemples, réponses)

### Exemple d’utilisation

```python
from intents_loader import load_intents

intents = load_intents("data/supptic_chatbot_standard.json")
```

---

## 4. Intégration de la Détection d’Intents dans l’API

**Fichier concerné :** `views.py`
**Endpoint modifié :** `/api/chatbot/ask/`

### Principe de fonctionnement

1. La question utilisateur est d’abord analysée par le système de détection d’intents.
2. Si un intent est détecté avec une confiance suffisante (≥ 0.8), la réponse associée est retournée immédiatement.
3. En cas d’échec, la logique existante basée sur TF-IDF est utilisée pour rechercher les FAQ pertinentes.

### Extrait de code

```python
@api_view(["POST"])
def ask_chatbot(request):
    user_query = request.data.get("question")
    if not user_query:
        return Response({"error": "La question est vide"}, status=400)

    intent, confidence, response = detect_intent(
        user_query, intent_model, intents
    )

    if confidence >= 0.8:
        return Response({
            "question": user_query,
            "intent": intent,
            "response": response,
            "confidence": confidence,
        })

    result = get_chatbot_response(user_query)
    return Response(result)
```

---

## 5. Sauvegarde du Modèle Entraîné

**Fichier concerné :** `train_intents.py`

### Description

Après l’entraînement, le modèle est sérialisé et sauvegardé dans un fichier `intent_classifier.pkl`.
Le dossier `models/` est automatiquement créé s’il n’existe pas.

### Extrait de code

```python
import os
import pickle

models_dir = "models"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

with open(os.path.join(models_dir, "intent_classifier.pkl"), "wb") as f:
    pickle.dump(model, f)
```

---

## 6. Gestion du Fallback Global

**Fichier concerné :** `intent_detection.py`

Si aucun intent n’est détecté avec un score de confiance suffisant, le chatbot fournit une réponse générique afin d’éviter une réponse incohérente ou erronée.

---

## 7. Tests et Validation

### Outil utilisé

* **Thunder Client**

### Méthodologie

* Envoi de requêtes POST vers l’endpoint `/api/chatbot/ask/`
* Vérification du comportement pour :

  * des questions connues
  * des formulations proches
  * des questions hors périmètre

### Exemple de requête

```http
POST /api/chatbot/ask/
Content-Type: application/json

{
  "question": "Quels sont les horaires de la bibliothèque ?"
}
```

### Exemple de réponse

```json
{
  "question": "Quels sont les horaires de la bibliothèque ?",
  "intent": "faq_horaires_bibliotheque",
  "response": "La bibliothèque est ouverte du lundi au vendredi de 8h à 18h, et le samedi de 9h à 13h.",
  "confidence": 0.92
}
```

---

## 8. Amélioration des Données d’Entraînement

### Actions réalisées

* Ajout d’exemples plus variés pour chaque intent
* Création de nouveaux intents pour couvrir des besoins spécifiques

### Exemple d’intent ajouté

```json
{
  "intent": "faq_stages_et_offres_d_emploi",
  "examples": [
    "Comment trouver un stage via SUP'PTIC ?",
    "Est-ce que SUP'PTIC propose des offres de stage ?"
  ],
  "responses": [
    "SUP'PTIC propose des offres de stage et d'emploi via son bureau d'insertion professionnelle."
  ]
}
```

---

## 9. Ajustement des Seuils de Confiance

* Le seuil de confiance a été abaissé de **0.8 à 0.7** afin d’accepter des formulations proches.
* Une réponse générique est retournée lorsque la confiance reste inférieure au seuil défini.

---

## 🧾 Résumé des Modifications

* Mise en place d’un système de détection d’intents
* Entraînement et sauvegarde d’un modèle de classification
* Chargement dynamique des intents depuis un fichier JSON
* Intégration de la détection d’intents dans l’API REST
* Ajout d’un mécanisme de fallback robuste
* Enrichissement des données d’entraînement
* Validation fonctionnelle via Thunder Client

---

Cette version est **présentable pour un rapport académique**, un **README GitHub**, ou une **documentation de soutenance**.
La prochaine étape logique serait d’ajouter un schéma d’architecture ou une section *limites et perspectives*.
