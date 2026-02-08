# 📌 ChatBot SUP'PTIC – Prototype

**Période :** 8 février — 13 février 2026  
**Réalisé par :** Club Informatique SUP'PTIC

---

## 🎯 Présentation

Ce **ChatBot SUP'PTIC** est un prototype développé par le Club Informatique SUP'PTIC. L'objectif est de fournir aux étudiants et personnels de SUP'PTIC un **outil interactif intelligent** capable de :

- Répondre automatiquement aux questions fréquentes (FAQ)
- Fournir des informations pertinentes sur les services et ressources de l'école

Ce projet est une démonstration concrète de l'application de technologies modernes en informatique pour créer des solutions utiles et efficaces.

---

## ⚙️ Fonctionnalités Principales

| Fonctionnalité                | Description                                                                         |
| ----------------------------- | ----------------------------------------------------------------------------------- |
| 🔍 **Recherche TF-IDF**       | Algorithme de similarité cosinus pour trouver la réponse pertinente parmi 1000+ FAQ |
| 🗄️ **Base de données Django** | Modèles complets : Utilisateurs, Catégories, FAQ, Vecteurs, Feedback                |
| 🌐 **API REST**               | Endpoints pour poser des questions, gérer les FAQ, collecter des statistiques       |
| 💬 **Interface web**          | Chat interactif en HTML/CSS/JS, design responsive, connexion directe à l'API        |
| 👍👎 **Feedback utilisateur** | Système de satisfaction intégré (like/dislike + commentaire optionnel)              |
| 📊 **Statistiques**           | Suivi des performances et taux de satisfaction par catégorie                        |

---

## 🧩 Architecture Projet

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

---

## 👥 Organisation des Équipes (10 personnes)

| Équipe                    | Effectif | Missions                                                          |
| ------------------------- | -------- | ----------------------------------------------------------------- |
| **Base de Données**       | 2        | Modèles Django, migrations, optimisation, scripts import/export   |
| **Structuration Données** | 4        | Génération massive CSV avec IA, nettoyage, validation (1000+ Q/R) |
| **Backend**               | 2        | API Django REST, TF-IDF, similarité cosinus, endpoints sécurisés  |
| **Frontend**              | 2        | Interface chat HTML/CSS/JS, design responsive, connexion API      |

---

## 📚 Dépendances Principales

```txt
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.26.2
```

---

## 🔧 API REST – Endpoints Principaux

| Méthode | Endpoint            | Description                                            |
| ------- | ------------------- | ------------------------------------------------------ |
| `POST`  | `/api/chatbot/ask/` | Poser une question → retourne top 3 résultats + scores |
| `GET`   | `/api/faq/`         | Lister toutes les FAQ (avec pagination)                |
| `GET`   | `/api/categories/`  | Lister les catégories de FAQ                           |
| `POST`  | `/api/feedback/`    | Enregistrer un feedback utilisateur (like/dislike)     |
| `GET`   | `/api/stats/`       | Statistiques : taux satisfaction, FAQ populaires       |

**Exemple de requête :**

```bash
curl -X POST http://localhost:8000/api/chatbot/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Quand sont les examens?"}'
```

**Réponse :**

```json
{
  "results": [
    {
      "id": 1,
      "question": "Quand se déroulent les examens?",
      "answer": "Les examens ont lieu...",
      "category": "Examens",
      "score": 0.92
    }
  ]
}
```

---

## 📅 Planning Détaillé (6 jours)

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
