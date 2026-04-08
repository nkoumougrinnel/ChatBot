# Historique des Changements

Ce dossier contient l'historique des modifications majeures du backend.

## Fichiers de changelog

### Systèmes implémentés

- `CHANGELOG_FEEDBACK_SYSTEM.md` - Système de feedback utilisateur
- `CHANGELOG_SIGNALS_SYSTEM.md` - Système de signaux Django

### Structure d'un changelog

Chaque changelog doit suivre ce format :

```markdown
# Changelog - [Nom du système/fonctionnalité]

## Vue d'ensemble

Description brève de la fonctionnalité implémentée.

## Changements apportés

### Modèles

- Ajout du modèle `Feedback`
- Modification du modèle `FAQ` (champ `popularity`)

### APIs

- Nouvel endpoint `/api/feedback/`
- Modification de `/api/faq/ask/`

### Signaux

- Signal `feedback_received` pour mise à  jour automatique
- Signal `faq_updated` pour recalcul des métriques

## Tests

- Tests unitaires pour les nouveaux modèles
- Tests d'intégration pour les APIs
- Tests de performance pour les signaux

## Migration

- Migration `0023_add_feedback_model.py`
- Script de migration des données existantes

## Déploiement

- Variables d'environnement à  ajouter
- Commandes de déploiement spécifiques
```

## Règles de contribution

- **Un fichier par fonctionnalité majeure**
- **Format chronologique** : changements les plus récents en haut
- **Liens vers commits/PRs** quand possible
- **Impact sur les autres équipes** clairement indiqué

