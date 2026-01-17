# ChatBot FAQ Management System - Vue d'ensemble

## 🎯 Objectif Global

Un système modulaire et extensible pour gérer les FAQ d'un chatbot, conçu en **phases successives** pour progresser graduellement du traitement manuel des données à une solution complètement automatisée.

## 📋 Phases du Projet

### **Phase 1 : Collecte et Validation des Données** (Actuelle)

Collecte semi-automatisée des FAQ depuis Google Sheets avec validation manuelle avant insertion en base de données SQLite.

- **Synchronisation** depuis Google Sheets
- **Validation manuelle** par l'équipe
- **Archivage** pour traçabilité
- **Base de données SQLite**

📖 [Documentation complète de Phase 1](phase-1/README.md)

### **Phase 2 : À définir**

_Roadmap en cours de définition_

### **Phase 3 et +**

_Évolutions futures du système_

## 🔧 Architecture Générale

Le système utilise une architecture par **phases indépendantes** :

- Chaque phase a ses propres scripts, configuration et données
- La base de données `db/faq.db` est **partagée** entre les phases
- Les logs sont centralisés dans `logs/`

📖 [Voir l'architecture détaillée](ARCHITECTURE.md)

## 📁 Structure du Projet

```
ChatBot/
├── phase-1/           # Phase 1 : Collecte & Validation
├── phase-2/           # Phase 2 (à venir)
├── db/                # Base de données partagée
├── logs/              # Logs de toutes les phases
├── docs/              # Documentation
└── requirements.txt   # Dépendances globales
```

## 🚀 Démarrage Rapide

### Installation

1. Cloner le dépôt
2. Installer les dépendances : `pip install -r requirements.txt`
3. Suivre le guide d'installation de Phase 1 : `docs/phase-1/SETUP.md`

### Utilisation Phase 1

```bash
python phase-1/scripts/sync.py              # Synchroniser les données
python phase-1/scripts/import_validated.py  # Importer les données validées
```

## 📊 Contribution et Évolution

Le projet est en **développement actif**. Les nouvelles phases seront ajoutées progressivement selon les besoins.

---

Pour plus de détails, consultez la [description des phases](PHASES.md) ou la [documentation de Phase 1](phase-1/README.md).
