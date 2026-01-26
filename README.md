# ChatBot - Système de Gestion FAQ Intelligent

> Un projet pour développer un chatbot conversationnel intelligent, alimenté par une FAQ gérée collectivement. **Actuellement en Phase 1 : Collecte et Validation des Données**.

## 🎯 Objectif

Créer un **chatbot FAQ intelligent** capable de :

1. **Répondre aux questions** des utilisateurs sur SUP'PTIC
2. **Apprendre** à partir d'une base FAQ collaborative et validée
3. **Évoluer** avec de nouvelles capacités dans les prochaines phases

## 📊 Phase 1 (Actuelle) : Collecte des Données

La Phase 1 est dédiée à la **collecte organisée des Questions/Réponses** par catégories d'étudiants :

- 👥 **Étudiants contributeurs** déposent des CSV par thème assigné
- ✅ **Validation manuelle** en présentiel par l'équipe
- 💾 **Stockage structuré** dans base SQLite
- 📦 **Archivage complet** pour traçabilité

## 📚 Documentation

| Document                                            | Description                         |
| --------------------------------------------------- | ----------------------------------- |
| 📖 [Vue d'ensemble](docs/PROJECT_OVERVIEW.md)       | Stratégie générale du projet        |
| 📋 [Phases](docs/PHASES.md)                         | Roadmap et phases futures           |
| 🏗️ [Architecture](docs/ARCHITECTURE.md)             | Schéma technique et flux de données |
| **🚀 [Phase 1 : Collecte](phase-1/docs/README.md)** | **Guide Phase 1 (vous êtes ici)**   |

## 🚀 Démarrage Rapide - Phase 1

### Pour les Étudiants Contributeurs

Consultez le **[Guide des Contributeurs](phase-1/docs/GUIDE_CONTRIBUTEURS.md)** pour savoir comment déposer votre fichier CSV dans votre catégorie assignée.

**Démarche simple :**

1. Identifiez votre catégorie et sous-thème assignés
2. Préparez un fichier CSV avec vos Questions/Réponses
3. Déposez-le dans : `phase-1/data/categories/[X]/[Y]/pending/`
4. L'équipe valide en présentiel

### Pour l'Équipe de Validation

Les fichiers déposés par les étudiants sont validés en réunion présentielle. Voir [Phase 1 README](phase-1/docs/README.md) pour la structure complète.

## 📁 Structure du Projet

```
ChatBot/
├── phase-1/                  # Phase 1 (ACTUELLE) : Collecte & Validation
│   ├── scripts/              # Scripts Python pour import/sync
│   ├── data/                 # Données
│   │   ├── categories/       # Dossiers par catégories étudiantes
│   │   ├── pending/          # En attente de validation
│   │   ├── processing/       # En cours de révision
│   │   ├── validated/        # Validées et prêtes
│   │   └── archived/         # Déjà intégrées à la BD
│   ├── config/               # Configuration (clés API, etc.)
│   └── docs/                 # Documentation Phase 1
│       ├── README.md                    # Vue d'ensemble Phase 1
│       ├── GUIDE_CONTRIBUTEURS.md       # Pour déposer un CSV
│       ├── MIGRATION_COMPLETE.md        # Historique des versions
│       ├── architecture_v1/             # Archive - ancien système
│       └── architecture_v2/             # Approche actuelle
│
├── phase-2/                  # Phase 2 (À VENIR)
├── ...                       # Phases futures
│
├── db/                       # Base de données partagée
│   └── faq.db                # SQLite - FAQ collectées
│
├── logs/                     # Logs de toutes les phases
│
├── docs/                     # Documentation générale
│   ├── PROJECT_OVERVIEW.md   # Vue d'ensemble projet
│   ├── ARCHITECTURE.md       # Architecture technique
│   └── PHASES.md             # Roadmap des phases
│
├── requirements.txt          # Dépendances Python
└── README.md                 # Ce fichier
```

## 🔧 Technologie

- **Language** : Python 3.8+
- **Base de données** : SQLite (`db/faq.db`)
- **Approche** : Collecte collaborative avec validation présentielle
- **Versioning** : Git (secrets non versionnés)

## ✨ Caractéristiques Phase 1

✅ **Collecte organisée** : Par catégories et sous-thèmes  
✅ **Contributions étudiantes** : Dépôt direct en CSV  
✅ **Validation présentielle** : Révision en réunion  
✅ **Traçable** : Archivage complet de l'historique  
✅ **Documenté** : Guides pour contributeurs et équipe  
✅ **Flexible** : Architecture V1 (Google Sheets) aussi disponible

## 🗺️ Roadmap Future

- **Phase 2** : Traitement du langage naturel (NLP)
- **Phase 3** : Interface utilisateur (chatbot conversationnel)
- **Phase 4** : Déploiement et optimisation
- **Phase 5** : Améliorations continues

## � Prochaines Étapes

### Vous êtes Étudiant Contributeur ?

👉 **[Lire le Guide des Contributeurs](phase-1/docs/GUIDE_CONTRIBUTEURS.md)**

### Vous êtes de l'Équipe de Validation ?

👉 **[Lire le README Phase 1](phase-1/docs/README.md)**

### Besoin d'en savoir plus ?

👉 **[Documentation Complète](docs/PROJECT_OVERVIEW.md)**
