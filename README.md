# ChatBot - Système de Gestion FAQ

Système de collecte et gestion des Questions/Réponses pour un chatbot intelligent.

## Objectif

Créer une base FAQ collaborative et validée pour alimenter un chatbot conversationnel capable de répondre aux questions sur SUP'PTIC.

## Phase Actuelle : Collecte des Données

Collecte organisée des Questions/Réponses par catégories d'étudiants :

- Étudiants contributeurs déposent des CSV par thème assigné
- Validation manuelle par l'équipe
- Stockage structuré dans base SQLite
- Archivage complet pour traçabilité

## Documentation

La documentation complète se trouve dans le dossier [collecte/docs/](collecte/docs/) :

## 🚀 Démarrage Rapide - Phase 1

### Pour les Étudiants Contributeurs

Consultez le **[Guide des Contributeurs](phase-1/docs/GUIDE_CONTRIBUTEURS.md)** pour savoir comment déposer votre fichier CSV dans votre catégorie assignée.
Démarrage Rapide

### Pour les Etudiants Contributeurs

Consultez le [Guide des Contributeurs](collecte/docs/GUIDE_CONTRIBUTEURS.md) pour savoir comment déposer votre fichier CSV.

**Démarche :**

1. Identifiez votre catégorie et sous-thème assignés
2. Préparez un fichier CSV avec vos Questions/Réponses
3. Déposez-le dans : `collecte/data/categories/[X]/[Y]/`
4. L'équipe valide et intègre à la base
   Structure du Projet

```
ChatBot/
├── collecte/                 # Collecte et validation des Q/R
│   ├── scripts/              # Scripts Python pour import/sync
│   ├── data/
│   │   ├── categories/       # Dossiers par catégories
│   │   │   ├── 1_inscriptions_admissions/
│   │   │   ├── 2_examens_evaluations/
│   │   │   ├── ...
│   │   │   └── category_manager.py
│   │   └── v1_collecte/      # Archive collecte v1
│   ├── config/               # Configuration
│   ├── docs/
│   │   ├── README.md         # Vue d'ensemble
│   │   ├── GUIDE_CONTRIBUTEURS.md
│   │   ├── architecture_v1/  # Archive
│   │   └── architecture_v2/  # Approche actuelle
│   └── tests/
│
├── db/                       # Base de données
│   └── faq.db
│
├── logs/                     # Logs
│
├── requirements.txt
└── README.md                 # Ce fichier
```

## 🔧 Technologie

- **Language** : Python 3.8+
- **Base de données** : SQLite (`db/faq.db`)
- **Approche** : Collecte collaborative avec validation présentielle
- **Versioning** : Git (secrets non versionnés)

## Technologie

- Python 3.8+
- SQLite (db/faq.db)
- Collecte collaborative avec validation présentielle
- Versioning : Gitque  
  ✅ **Documenté** : Guides pour contributeurs et équipe  
  ✅ \*Caracteristiques

## Prochaines Etapes

Contributions étudiantes → Validation → Base de données → ChatBot (phases futures)
