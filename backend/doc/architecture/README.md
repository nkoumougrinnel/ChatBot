# Architecture Système

Ce dossier contient la documentation architecturale du backend Django.

## Documents disponibles

### Architecture générale

- `ARCHITECTURE.md` - Vue d'ensemble de l'architecture
- `PREPROCESSING_COMPARAISON.md` - Comparaison des méthodes de préprocessing

### Diagrammes et schémas

- Diagrammes d'architecture (à  ajouter)
- Schémas de base de données
- Diagrammes de flux

## Structure recommandée

### Vue d'ensemble

- **Architecture globale** : Django + DRF + PostgreSQL
- **Applications Django** : faq, users, chatbot
- **Services externes** : Ollama, FAISS (Phase 2)

### Composants détaillés

#### Modèle de données

- Schéma relationnel
- Contraintes et indexes
- Stratégies de dénormalisation

#### APIs REST

- Endpoints et méthodes HTTP
- Sérialiseurs et validation
- Gestion d'erreurs

#### Moteur de recherche

- TF-IDF (Phase 1)
- RAG avec FAISS (Phase 2)
- Métriques de similarité

### Performance et scalabilité

- Optimisations de requêtes
- Cache et indexation
- Stratégies de déploiement

## Mise à  jour

La documentation architecturale doit être mise à  jour :

- **Après chaque changement majeur**
- **Avant les revues d'architecture**
- **Lors des changements de phase**

## Références

- [Django Documentation](https://docs.djangoproject.com/)
- [DRF Documentation](https://www.django-rest-framework.org/)
- [FAISS Documentation](https://faiss.ai/)

