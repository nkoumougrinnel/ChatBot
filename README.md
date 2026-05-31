# ChatBot SUP'PTIC – Phase 2

**Réalisé par :** Club Informatique SUP'PTIC

---

## Passage à la Phase 2

Le projet a maintenant quitté la Phase 1 pour entrer en **Phase 2**. Les documents de la Phase 1 restent disponibles dans `docs/phase1/` à titre historique, mais l'activité principale se concentre désormais sur :

- `docs/phase2/architecture/`
- `docs/phase2/documentation_technique/`
- `docs/phase2/roadmap/`

---

## Présentation

Ce **ChatBot SUP'PTIC** est désormais en **Phase 2**, avec une évolution majeure vers une architecture RAG (Retrieval-Augmented Generation). Le projet conserve les bases du chatbot FAQ, mais ajoute :

- une architecture hybride RAG + TF-IDF
- un index FAISS pour la recherche vectorielle
- un LLM local via Ollama pour enrichir les réponses
- une interface plus riche avec historique de conversation

---

## Fonctionnalités principales

<<<<<<< HEAD
```
ChatBot/
├── .venv/              # Environnement virtuel Python
│
├── backend/
│   ├── config/          # Paramètres Django (settings, urls, wsgi)
│   ├── faq/             # App gestion FAQ
│   ├── chatbot/         # App algorithme TF-IDF et prétraitement texte
│   ├── users/           # App utilisateurs + feedback
│   ├── manage.py
│   └── db.sqlite3       # Base de données SQLite
│
├── frontend/
│   ├── index.html       # Page principale du chatbot
│   ├── css/
│   │   └── styles.css   # Styles responsive
│   ├── js/
│   │   └── app.js       # Logique du chatbot (fetch API, UI)
│   └── assets/
│
├── data/
│   ├── csv/             # Fichiers CSV générés par catégories/sous-thèmes
│   └── scripts/         # Scripts import/export
│
├── docs/
│   └── README_API.md
│
├── README.md            # Documentation principale (ce fichier)
└── requirements.txt     # Dépendances Python
```
=======
| Fonctionnalité           | Description                                                                    |
| ------------------------ | ------------------------------------------------------------------------------ |
| Pipeline RAG             | Recherche de documents par embeddings MiniLM, index FAISS, puis génération LLM |
| Bascule RAG / TF-IDF     | Passage automatique entre RAG et TF-IDF selon le score de confiance            |
| API REST v2              | Endpoint `/api/chatbot/ask/` amélioré avec fallback, sources et méthode        |
| Historique conversation  | Stockage local (localStorage) des conversations et navigation multi-tours      |
| Retour utilisateur       | Feedback positif/négatif avec traçage de la méthode utilisée (RAG ou TF-IDF)   |
| Passage au React         | Interface web migrée vers React, chat responsive, badge de méthode et streaming SSE |
>>>>>>> 63bc96bc834531acd7719edd6e3541982a2ed93e

---

## Architecture du projet

Le dépôt est organisé ainsi :

- `backend/` : application Django, API, gestion des FAQ et du moteur de similarité
- `frontend/` : interface utilisateur et application PWA
- `data/` : jeux de données, scripts et documentation de données
- `docs/` : documentation générale et par phase
- `requirements.txt` : dépendances Python

---

## Documentation Phase 2

La documentation de la Phase 2 est le bon point d'entrée :

- `docs/phase2/README.md` : résumé de la Phase 2
- `docs/phase2/architecture/` : documents d'architecture système
- `docs/phase2/documentation_technique/` : documentation technique
- `docs/phase2/roadmap/` : feuille de route Phase 2

Pour les éléments de configuration et de déploiement, consultez également :

- `docs/setup/NGROK_SETUP.md`
- `backend/doc/` : spécifications backend détaillées
- `frontend/README.md` : documentation frontend

---

## Installation rapide

1. Créez et activez un environnement virtuel :
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. Installez les dépendances :
   ```powershell
   pip install -r requirements.txt
   ```
3. Lancez le serveur Django :
   ```powershell
   python backend/manage.py runserver
   ```
4. Ouvrez `http://localhost:8000/` dans votre navigateur.

---

## Notes

<<<<<<< HEAD
### **Jour 1-2** : Fondations et Premières Vagues

- Initialiser dépôt Git et projet Django
- Créer modèles Django (FAQ, Utilisateurs, Feedback, Vecteurs)
- Générer 400 Q/R (par vagues de 100)
- Implémenter prétraitement texte basique
- **Objectif :** 400 Q/R en base de données

### **Jour 3-4** : Algorithme et Intégration

- Implémenter TF-IDF vectorizer
- Créer endpoints API REST
- Générer 600 Q/R supplémentaires
- Intégrer frontend basique
- **Objectif :** 1000 Q/R, API complète, interface de base

### **Jour 5** : Documentation et Démo

- Documentation API complète (`README_API.md`)
- Système feedback opérationnel
- Pages "statistiques" et "À propos"
- Répétition démo (3x minimum)
- **Objectif :** Démonstration préparée et documentée

### **Jour 6** : Finalisation et Livraison

- Derniers ajustements UI/UX
- Déploiement sur serveur test
- Finalisation README principal
- **Démonstration officielle (18h)**

---

## 📦 Livrables Attendus (13 février 18h)

✅ **Code**

- Projet Django complet (3 apps : `faq`, `chatbot`, `users`)
- Frontend HTML/CSS/JS fonctionnel avec feedback
- Base de données avec 1000+ Q/R validées
- API REST testée et fonctionnelle

✅ **Documentation**

- `README.md` complet (ce fichier)
- `README_API.md` (spécifications et exemples)

✅ **Démonstration**

- Application déployée et accessible
- Présentation PowerPoint (10-15 slides)
- Scénario démo préparé et répété
- 10 questions test impressionnantes

---

## 📊 Indicateurs de Succès

| Critère                  | Objectif | Mesure                        |
| ------------------------ | -------- | ----------------------------- |
| **Q/R en base**          | 1000+    | `SELECT COUNT(*) FROM faq`    |
| **Taux réponse**         | >70%     | Questions avec score > 0.6    |
| **API fonctionnelle**    | 100%     | Tous endpoints testés ✓       |
| **Interface utilisable** | ✓        | Chat + feedback opérationnels |
| **Documentation**        | ✓        | README + API + BD complètes   |
| **Démo prête**           | ✓        | Scénario testé 3x minimum     |

---

## ⚠️ Points d'Attention Critiques

### Risques Identifiés

- **Synchronisation équipes** → Réunions quotidiennes (matin + soir)
- **Qualité vs Quantité** → Validation systématique 20% des Q/R
- **Scope creep** → NE PAS ajouter fonctionnalités non prévues
- **Fatigue production** → Pauses régulières, rotation des tâches

### Bonnes Pratiques

- 🔄 **Commits Git** : min. 2 par personne par jour
- 💬 **Communication** : groupe Telegram/WhatsApp actif
- 🐛 **Bug tracking** : fichier partagé centralisé
- ✅ **Tests** : après chaque feature importante
- ☕ **Pauses** : régulières pour éviter la fatigue

---

## 🚀 Installation et Lancement Rapide

### Prérequis

- Python 3.10+
- pip
- Git

### Setup (Windows PowerShell)

```powershell
# Cloner et entrer dans le dossier
git clone <repository-url>
cd chatbot-supptic

# Créer environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installer dépendances
pip install -r requirements.txt

# Initialiser base de données
cd backend
python manage.py makemigrations
python manage.py migrate

# (Optionnel) Charger données démo
python manage.py loaddata fixtures/demo_faq.json

# Lancer serveur Django
python manage.py runserver
```

### Accès Application

- **Backend API** : http://localhost:8000/api/
- **Frontend** : Ouvrir `frontend/index.html` dans navigateur

---

## 🔧 Modules Clés à Implémenter

### Backend (`chatbot/utils.py`)

```python
def preprocess_text(text: str) -> str:
    """Tokenisation, suppression stopwords FR, normalisation."""

def train_vectorizer(corpus: List[str]) -> TfidfVectorizer:
    """Entraîner TF-IDF sur le corpus FAQ."""

def compute_tfidf_vector(text: str, vectorizer) -> np.ndarray:
    """Vecteur TF-IDF pour une requête."""

def compute_cosine_similarity(vec1, vec2) -> float:
    """Similarité cosinus entre deux vecteurs."""

def find_best_faq(question: str, top_k: int = 3) -> List[Dict]:
    """Trouver top K réponses + scores."""
```

---

## 📚 Documentation Complémentaire

Les fichiers suivants seront générés au cours du projet :

- **`README_API.md`** : Spécifications API détaillées, exemples cURL, authentification

---

## 🎯 Objectif Final

✨ **1000+ Q/R validées**  
✨ **Algorithme TF-IDF robuste**  
✨ **API REST sécurisée**  
✨ **Interface web responsive**  
✨ **Documentation technique complète**  
✨ **Démonstration impressionnante**

---

**Let's build something amazing together!** 🚀
=======
- Le contenu principal de la Phase 2 est dans `docs/phase2/`.
- Les documents de la Phase 1 sont conservés dans `docs/phase1/` pour référence historique.
- Vérifiez l'encodage UTF-8 si vous éditez des fichiers de documentation.
>>>>>>> 63bc96bc834531acd7719edd6e3541982a2ed93e
