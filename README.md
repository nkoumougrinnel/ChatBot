# ChatBot

> Un projet modulaire et extensible pour construire un chatbot intelligent, conçu en phases successives.

## 🎯 Qu'est-ce que c'est ?

**ChatBot** est un projet complet visant à développer un chatbot intelligent. Le projet est organisé en **phases**, chacune ajoutant des fonctionnalités.

### Phase 1 (Actuelle) : FAQ Management System

Gestion et collecte des FAQ depuis Google Sheets avec validation manuelle :

- Synchronisation depuis Google Sheets
- Validation manuelle par l'équipe
- Insertion en base SQLite
- Archivage pour traçabilité

Les futures phases ajouteront de nouvelles capacités (traitement du langage naturel, interface utilisateur, déploiement, etc.).

## 📚 Documentation

| Lien                                                    | Description                     |
| ------------------------------------------------------- | ------------------------------- |
| 📖 [Vue d'ensemble du projet](docs/PROJECT_OVERVIEW.md) | Voir les phases et la roadmap   |
| 📋 [Description des phases](docs/PHASES.md)             | Détails de chaque phase         |
| 🏗️ [Architecture générale](docs/ARCHITECTURE.md)        | Flux de données et organisation |
| 🚀 [Phase 1 : Installation](docs/phase-1/SETUP.md)      | Guide d'installation            |
| ⚙️ [Phase 1 : Utilisation](docs/phase-1/USAGE.md)       | Comment utiliser les scripts    |

## 🚀 Démarrage Rapide

### Installation

```bash
# 1. Cloner le dépôt
git clone <url_du_repo>
cd ChatBot

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer Phase 1
# Voir docs/phase-1/SETUP.md pour la configuration initiale
```

### Premiers pas avec Phase 1

```bash
# Récupérer les données depuis Google Sheets
python phase-1/scripts/sync.py

# [L'équipe valide les fichiers CSV manuellement]

# Importer les données validées en base
python phase-1/scripts/import_validated.py
```

👉 **Guide complet** : [docs/phase-1/USAGE.md](docs/phase-1/USAGE.md)

## 📁 Structure du Projet

```
ChatBot/
├── phase-1/              # Phase 1 : Collecte & Validation
│   ├── scripts/          # Scripts Python
│   ├── data/             # Données temporaires (pending, validated, archived)
│   ├── config/           # Configuration
│   └── tests/            # Tests
│
├── phase-2/              # Phase 2 (à venir)
├── ...
│
├── db/                   # Base de données partagée
│   └── faq.db            # SQLite
│
├── logs/                 # Logs de toutes les phases
│
├── docs/                 # Documentation complète
│   ├── PROJECT_OVERVIEW.md    # Vue d'ensemble
│   ├── ARCHITECTURE.md         # Schéma technique
│   ├── PHASES.md               # Description des phases
│   ├── phase-1/                # Doc Phase 1
│   │   ├── README.md
│   │   ├── SETUP.md
│   │   ├── USAGE.md
│   │   ├── Gestion FAQ.tex     # Documentation LaTeX
│   │   └── Gestion FAQ.pdf
│   ├── phase-2/                # Doc Phase 2 (à venir)
│   └── common/                 # Documentation partagée
│
├── requirements.txt      # Dépendances Python
└── README.md            # Ce fichier
```

## 🔧 Technologie

- **Language** : Python 3.8+
- **Base de données** : SQLite
- **API** : Google Sheets API
- **Librairies** : gspread, pandas, etc.

## ✨ Caractéristiques

✅ **Modulaire** : Phases indépendantes et extensibles  
✅ **Traçable** : Archivage et logging complets  
✅ **Sécurisé** : Clés d'accès non versionnées  
✅ **Documenté** : Documentation pour chaque phase  
✅ **En développement** : Évolution progressive

## 🐛 Problèmes ?

Voir la section troubleshooting :

- 📖 [Phase 1 - Troubleshooting](docs/phase-1/USAGE.md#-troubleshooting)
- 📖 [Phase 1 - Installation](docs/phase-1/SETUP.md)

## 📄 License

À définir

## 👤 Auteur

À définir

---

**Prêt à commencer ?** 👉 [Installation Phase 1](docs/phase-1/SETUP.md)

**Besoin d'aide ?** 👉 [Documentation complète](docs/PROJECT_OVERVIEW.md)
