# Déploiement et Production

Documentation relative au déploiement, à  la mise en production et à  l'infrastructure.

## Types de documents

### Déploiement

- `deployment-heroku.md` - Déploiement sur Heroku
- `deployment-ngrok.md` - Configuration Ngrok pour le développement
- `ci-cd-pipeline.md` - Pipeline CI/CD

### Infrastructure

- `infrastructure-overview.md` - Vue d'ensemble de l'infrastructure
- `database-setup.md` - Configuration de la base de données
- `environment-variables.md` - Variables d'environnement

## Structure recommandée

Pour chaque document de déploiement :

- **Contexte** : Quand et pourquoi utiliser cette méthode
- **Prérequis** : Environnements et outils nécessaires
- **à‰tapes détaillées** : Commandes et configurations
- **Vérifications** : Tests post-déploiement
- **Résolution de problèmes** : Erreurs courantes

## Variables d'environnement

Documenter toutes les variables dans `environment-variables.md` :

- `DEBUG` : Mode debug (True/False)
- `SECRET_KEY` : Clé secrète Django
- `DATABASE_URL` : URL de connexion base de données
- `OLLAMA_BASE_URL` : URL du service Ollama

