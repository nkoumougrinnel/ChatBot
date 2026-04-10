# Documentation Backend

Documentation technique du backend Django du projet ChatBot.

## Arborescence

```
backend/doc/
├── api/              # Documentation des APIs REST
├── architecture/     # Architecture système et design
├── changelog/        # Historique des changements
├── config/           # Configuration et environnement
├── deployment/       # Déploiement et production
├── maintenance/      # Maintenance et monitoring
├── models/           # Modèles de données et schémas
└── reports/          # Rapports et analyses
```

## Règles de contribution

### Nommage des fichiers

- Utiliser des noms descriptifs en minuscules avec tirets : `guide-mise-en-route.md`
- Préfixer par type si nécessaire : `api-faq-endpoints.md`

### Structure des documents

- Commencer par un titre principal (`# Titre`)
- Ajouter une description courte
- Utiliser des sections claires (`## Section`)
- Terminer par des références si nécessaire

### Où déposer quoi ?

- **Nouveau guide** → `guides/`
- **Documentation API** → `api/`
- **Modèle de données** → `models/`
- **Problème de prod** → `maintenance/`
- **Déploiement** → `deployment/`
- **Changement majeur** → `changelog/`
- **Rapport d'analyse** → `reports/`

## Exemples d'utilisation

### Ajouter un guide

1. Créer `backend/doc/guides/mon-guide.md`
2. Suivre la structure standard
3. Référencer dans les README appropriés

### Documenter une API

1. Créer `backend/doc/api/nom-api.md`
2. Inclure endpoints, paramètres, exemples
3. Mettre à jour `api/README.md`

### Signaler un incident

1. Créer `backend/doc/maintenance/incident-YYYY-MM-DD.md`
2. Décrire le problème, la solution, les leçons apprises
