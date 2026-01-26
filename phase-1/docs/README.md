# Phase 1 : Collecte et Validation des Données

## 📝 Description

Phase 1 du ChatBot FAQ Management System - Système V2.

Un système automatisé pour gérer les FAQ d'un chatbot, avec collecte par catégories d'étudiants, validation et insertion en base de données SQLite.

**Note** : Cette phase inclut l'architecture V2 actuelle. Voir [architecture_v1/](architecture_v1/) pour la documentation de l'ancienne approche.

## ✨ Fonctionnalités

- **Collecte par catégories** : Étudiants déposent des CSV par thème assigné
- **Validation manuelle** : Processus de révision par l'équipe avant insertion
- **Archivage automatique** : Traçabilité historique des fichiers traités
- **Base de données SQLite** : Stockage structuré des FAQ
- **Logging** : Suivi des succès/échecs des opérations

## 📁 Structure

```
phase-1/

├── scripts/
│   ├── sync.py                  # Script de collecte Google Sheets (V1)
│   ├── import_validated.py      # Script d'insertion (data/validated → db)
│   └── reset_and_import.py      # Script de reset et réimport
│
├── data/
│   ├── last_row.txt             # Suivi du dernier index traité (V1)
│   ├── categories/              # V2: Données par catégories d'étudiants
│   │   ├── 1_inscriptions_admissions/
│   │   ├── 2_examens_evaluations/
│   │   ├── ...
│   │   └── 9_vie_pratique/
│   ├── pending/                 # Fichiers en attente de validation
│   ├── processing/              # Fichiers en cours de traitement
│   ├── validated/               # Fichiers corrigés et validés
│   └── archived/                # Fichiers déjà insérés (trace)
│
├── config/
│   └── faq-service-key.json     # Clé de service Google (V1, non versionnée)
│
├── docs/
│   ├── architecture_v1/         # Ancienne approche (Google Sheets)
│   │   ├── Gestion FAQ.tex
│   │   ├── Gestion FAQ.pdf
│   │   └── images/
│   ├── architecture_v2/         # Approche actuelle (Catégories étudiants)
│   │   ├── Gestion ChatBot FAQ.tex
│   │   ├── Gestion ChatBot FAQ.pdf
│   │   └── images/
│   ├── README.md                # Ce fichier
│   ├── GUIDE_CONTRIBUTEURS.md   # Pour les équipes contributeurs
│   └── MIGRATION_COMPLETE.md    # Historique de la migration V1→V2
│
└── tests/                       # Vide (fichiers de test à ajouter)
```

## 🔄 Cycle de Vie des Fichiers (V2)

```
Étudiants                    Équipe Validation               BD
   ↓                              ↓                            ↓
data/categories/             data/pending/               faq.db
├─ 1_inscriptions/        ──→ Fichier reçu        ──→  Insertion
├─ 2_examens/             ──→ Review+Correction   ──→  Archivage
├─ 3_specialisation/      ──→ data/validated/     ──→
└─ ...
```

### Étapes détaillées

1. **Étudiants** déposent des CSV dans `phase-1/data/categories/[X]/[Y]/pending/`
2. Fichier auto-transféré vers `phase-1/data/pending/` pour validation globale
3. L'équipe examine et corrige → `phase-1/data/processing/`
4. Approbation → `phase-1/data/validated/`
5. **import_validated.py** lit, insère dans `db/faq.db`, archive dans `data/archived/`

**Architecture V1** : Approche Google Sheets (voir [docs/architecture_v1/](architecture_v1/))

## 📖 Guides

- [Guide pour Contributeurs Étudiants](GUIDE_CONTRIBUTEURS.md) - **À consulter pour déposer un CSV**
- 📚 [Historique Migration V1→V2](MIGRATION_COMPLETE.md)

## 📋 Documentation Architecturale

- **V2 (Actuelle)** : [docs/architecture_v2/](architecture_v2/) - Approche par catégories étudiants
- **V1 (Archive)** : [docs/architecture_v1/](architecture_v1/) - Approche Google Sheets

## 🔐 Sécurité

- La clé de service Google (`phase-1/config/faq-service-key.json`) n'est pas versionnée (V1 only)
- Seules les données validées sont insérées en base
- Archivage pour traçabilité complète

---

Pour la vue d'ensemble du projet : 📖 [Aller au README principal](../PROJECT_OVERVIEW.md)
