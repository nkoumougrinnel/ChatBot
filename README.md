# 📌 ChatBot SUP'PTIC – Version 1.0.0

**Période :** 8 février — 13 février 2026  
**Réalisé par :** Club Informatique SUP'PTIC

---

## 🎯 Présentation

Ce **ChatBot SUP'PTIC** est la **version 1.0.0** développée par le Club Informatique SUP'PTIC. L'objectif est de fournir aux étudiants et personnels de SUP'PTIC un **outil interactif intelligent** capable de :

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
│   ├── doc/             # 📚 Documentation backend
│   │   ├── api/         # Spécifications API REST
│   │   ├── architecture/# Architecture et schémas
│   │   ├── changelog/   # Historique des modifications
│   │   ├── config/      # Configuration CORS, déploiement
│   │   └── reports/     # Rapports de tests et performances
│   ├── manage.py
│   └── db.sqlite3       # Base de données SQLite
│
├── frontend/
│   ├── pwa/             # 📱 Application PWA indépendante
│   │   ├── index.html   # Interface PWA
│   │   ├── manifest.json
│   │   ├── service-worker.js
│   │   ├── css/
│   │   ├── js/
│   │   ├── doc/         # 📚 Documentation PWA
│   │   │   └── GUIDE_PWA.md
│   │   └── icons/
│   ├── README.md        # Documentation frontend
│   └── start_server.py # Serveur de développement
│
├── docs/                # 📚 Documentation générale
│   ├── README.md        # Vue d'ensemble du projet
│   └── setup/
│       └── NGROK_SETUP.md # Configuration Ngrok
│
├── README.md            # Documentation principale (ce fichier)
└── requirements.txt     # Dépendances Python
```

---

## � Documentation du Projet

Le projet dispose d'une documentation complète organisée par domaine :

### 📖 Documentation Générale

- **`README.md`** (ce fichier) - Vue d'ensemble, architecture, installation
- **`docs/README.md`** - Documentation complémentaire du projet
- **`docs/setup/NGROK_SETUP.md`** - Configuration et déploiement avec Ngrok

### 🔧 Documentation Backend

Située dans `backend/doc/` :

- **`api/`** - Spécifications complètes des endpoints REST, exemples d'usage
- **`architecture/`** - Schémas d'architecture, modèles de données, workflows
- **`changelog/`** - Historique des modifications par blocs fonctionnels
- **`config/`** - Configuration CORS, déploiement, sécurité
- **`reports/`** - Rapports de tests, performances, métriques

### 🎨 Documentation Frontend

- **`frontend/README.md`** - Guide d'utilisation de l'interface web
- **`frontend/pwa/doc/GUIDE_PWA.md`** - Documentation complète de l'application PWA

### 📱 Documentation PWA

- **`frontend/pwa/doc/GUIDE_PWA.md`** - Installation, configuration, déploiement PWA
  - Fonctionnalités offline, service worker, manifest
  - Personnalisation des couleurs et icônes
  - Déploiement sur Netlify/Vercel
  - Dépannage et optimisation

---

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

## � Historique des Versions

### Version 1.0.0 (Base)

- **Date :** Avril 2026
- **Statut :** Version de base stable
- **Fonctionnalités :**
  - Recherche TF-IDF avec similarité cosinus
  - Base de données Django avec 1000+ FAQ
  - API REST complète
  - Interface web responsive
  - Système de feedback utilisateur
  - Application PWA avec fonctionnalités offline
  - Documentation complète
- **Technologies :** Django 4.2.7, scikit-learn, spaCy, HTML5/CSS3/JS

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

# Charger les données FAQ depuis le script
python data/scripts/load_json_data_sqlite.py

# Lancer serveur backend Django (dans un terminal)
python start_server.py

# Lancer serveur frontend (dans un autre terminal)
cd ../frontend
python start_server.py
```

### Accès aux applications

- **API Backend** : http://localhost:8000
- **Interface Frontend** : http://localhost:8080
- **Application PWA** : http://localhost:8080/pwa/