# Phases du Projet ChatBot FAQ Management System

## Vue d'ensemble

Le projet est conçu en **phases successives** pour progresser graduellement vers une solution complète et autonome.

## 📌 Phase 1 : Collecte et Validation des Données

**Status** : 🟢 En cours

**Objectif** : Automatiser partiellement la collecte de FAQ depuis Google Sheets avec validation manuelle avant insertion en base.

### Caractéristiques

- Synchronisation depuis Google Sheets
- Stockage temporaire avec workflow (pending → processing → validated → archived)
- Validation manuelle par l'équipe
- Insertion en base SQLite avec traçabilité
- Logging complet de toutes les opérations

### Composants

- `phase-1/scripts/sync.py` : Collecte depuis Google Sheets
- `phase-1/scripts/import_validated.py` : Insertion en base
- `phase-1/scripts/reset_and_import.py` : Utilitaire de reset

### Données

- Entrées : Google Sheets
- Sortie : `db/faq.db`
- Format intermédiaire : CSV horodaté

---

## 🔳 Phase 2 : À Définir

**Status** : 🟡 Planifiée

Évolution proposée : _À discuter_

Possibilités :

- Enrichissement automatique des FAQ (lemmatisation, tags, synonymes)
- Détection et déduplication
- Indexation sémantique
- Interface de gestion web

---

## 🔳 Phases Futures (3+)

À définir selon les besoins du projet.

---

## Principes de Conception

✅ **Modularité** : Chaque phase est indépendante dans son implémentation  
✅ **Partage de ressources** : BD et logs centralisés  
✅ **Évolutivité** : Facile d'ajouter de nouvelles phases  
✅ **Traçabilité** : Archivage et logging complets

---

Pour plus d'informations :

- 📖 [Vue d'ensemble du projet](PROJECT_OVERVIEW.md)
- 📖 [Architecture générale](ARCHITECTURE.md)
- 📖 [Documentation Phase 1](phase-1/README.md)
