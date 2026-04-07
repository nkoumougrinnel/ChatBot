# Données - Dataset FAQ ChatBot

Ce dossier contient les données d'entraînement et de test pour le chatbot SUP'PTIC.

## Structure

```
data/
â”œâ”€â”€ json/
â”‚   â”œâ”€â”€ drafts/         # Fichiers JSON en brouillon avant validation
â”‚   â”œâ”€â”€ validated/      # Fichiers JSON validés prêts à  être importés en base
â”‚   â””â”€â”€ donnees_exemples.json  # Exemple de dataset formaté
â”œâ”€â”€ scripts/           # Outils de traitement des données
â””â”€â”€ doc/               # Documentation des données
    â””â”€â”€ README.md      # Format et structure des données
```

## Format des données

Les données FAQ sont structurées au format JSON avec le schéma suivant :

```json
{
  "id": "faq_001",
  "categorie": "Admissions",
  "sous_theme": "Dossier d'inscription",
  "question": "Quels documents fournir pour s'inscrire à  SUP'PTIC ?",
  "reponse_enrichie": "Le dossier comprend : formulaire d'inscription, photocopie du diplôme, acte de naissance, photos d'identité. Tous les documents doivent être fournis en 2 exemplaires.",
  "exemples": [
    "Comment s'inscrire à  SUP'PTIC ?",
    "Quelles pièces fournir pour l'admission ?",
    "Qu'est-ce qu'il faut pour le dossier d'entrée ?"
  ],
  "sources": ["Service des admissions"],
  "date_creation": "2026-04-07",
  "version": "2.0",
  "valide": true
}
```

### Champs

- **id** : Identifiant unique (format : `faq_[numero sur 3 chiffres]`)
- **categorie** : Domaine principal (Admissions, Formation, Frais, etc.)
- **sous_theme** : Précision sur le sujet
- **question** : Question principale de référence
- **reponse_enrichie** : Réponse complète et détaillée
- **exemples** : Liste de formulations alternatives de la question
- **sources** : Liste des sources d'information
- **date_creation** : Date de création (format YYYY-MM-DD)
- **version** : Version du contenu (format semver)
- **valide** : Statut de validation (boolean)

## Exemple de données

```json
{
  "id": "faq_001",
  "categorie": "Admissions",
  "sous_theme": "Dossier d'inscription",
  "question": "Quels documents fournir pour s'inscrire à  SUP'PTIC ?",
  "reponse_enrichie": "Le dossier comprend : formulaire d'inscription, photocopie du diplôme, acte de naissance, photos d'identité. Tous les documents doivent être fournis en 2 exemplaires.",
  "exemples": [
    "Comment s'inscrire à  SUP'PTIC ?",
    "Quelles pièces fournir pour l'admission ?",
    "Qu'est-ce qu'il faut pour le dossier d'entrée ?"
  ],
  "sources": ["Service des admissions"],
  "date_creation": "2026-04-07",
  "version": "2.0",
  "valide": true
}
```

## Flux de publication

Les données suivent le flux suivant :

- Les fichiers JSON non validés sont placés dans `data/json/drafts/`
- Après relecture et validation, les fichiers sont déplacés vers `data/json/validated/`
- L'équipe base de données importe les fichiers de `data/json/validated/` en base

## Organisation par domaine

Les fichiers sont organisés par domaine fonctionnel :

- `faq_admissions.json` - Questions sur les admissions
- `faq_frais.json` - Tarifs et frais de scolarité
- `faq_formations.json` - Programmes et filières
- `faq_vie_etudiante.json` - Vie étudiante et campus
- etc.

## Qualité des données

### Critères

- **Pertinence** : Questions réellement posées par les étudiants
- **Exactitude** : Réponses vérifiées auprès des sources officielles
- **Diversité** : Formulation variée des questions
- **Cohérence** : Terminologie uniforme

### Maintenance

- Mise à  jour régulière des informations
- Validation croisée des sources
- Tests d'intégration avec le moteur de recherche

