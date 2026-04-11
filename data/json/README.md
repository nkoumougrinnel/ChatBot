# Documentation des données FAQ

Informations détaillées sur la structure, la qualité et l'évolution du dataset.

## Schéma de données

### Structure complète

```json
{
  "id": "string (requis, format: faq_[001-999])",
  "categorie": "string (requis)",
  "sous_theme": "string (requis)",
  "question": "string (requis)",
  "reponse_enrichie": "string (requis)",
  "exemples": "array[string] (requis, min: 1)",
  "sources": "array[string] (requis, min: 1)",
  "date_creation": "string (requis, format: YYYY-MM-DD)",
  "version": "string (requis, format: semver)",
  "valide": "boolean (requis)"
}
```

## Conventions de nommage

### IDs

Format : `faq_[numero sur 3 chiffres]`

- **faq_001** à  **faq_999** : Numérotation séquentielle
- Pas de gaps dans la numérotation
- Réservation des premiers numéros pour les FAQs critiques

Exemples :

- `faq_001` : Admissions - Documents requis
- `faq_002` : Frais - Tarifs scolarité
- `faq_003` : Formation - Programmes disponibles

### Catégories principales

1. **Introduction** - Présentation de l'établissement
2. **Admissions** - Conditions d'accès, procédures
3. **Formation** - Programmes, filières, diplômes
4. **Frais** - Tarifs, bourses, paiements
5. **Vie étudiante** - Campus, hébergement, associations
6. **International** - à‰changes, partenariats
7. **Carrières** - Insertion professionnelle, stages
8. **Services** - Bibliothèque, informatique, santé

## Qualité des données

### Critères d'acceptation

- **Pertinence** : Questions fréquemment posées
- **Exactitude** : Informations vérifiées auprès des sources officielles
- **Diversité** : Au moins 3 formulations alternatives dans `exemples`
- **Clarté** : `reponse_enrichie` complète et compréhensible
- **Actualité** : `date_creation` récente et `version` à  jour
- **Validation** : `valide` = true après contrôle qualité

### Métriques de qualité

- **Couverture** : Tous les domaines importants représentés
- **Actualité** : Informations à  jour (vérification semestrielle)
- **Cohérence** : Terminologie uniforme
- **Testabilité** : Données utilisables pour les tests

## Sources des données

### Sources primaires

- Site officiel : https://e-supptic.cm/
- Documents administratifs
- Entretiens avec le personnel
- Retours des étudiants

### Sources secondaires

- Forums étudiants
- Réseaux sociaux
- Anciens élèves
- Partenaires institutionnels

## à‰volution du dataset

### Versionnement

- **v1.0** : Dataset initial (127 FAQs)
- **v1.1** : Ajout catégories International et Services
- **v1.2** : Enrichissement exemples (+30% par FAQ)

## Flux de publication

- Les fichiers JSON sont d'abord préparés en tant que brouillons dans `data/json/drafts/`
- La validation porte sur le format, la qualité des réponses et la cohérence des métadonnées
- Une fois validés, les fichiers sont transférés vers `data/json/validated/`
- L'équipe base de données utilise `data/json/validated/` pour l'insertion en base

## Intégration

### Avec le moteur TF-IDF

- Utilisation des `exemples` + `question` pour l'indexation
- `reponse_enrichie` pour les réponses du bot
- `categorie` et `sous_theme` pour le filtrage

### Avec le RAG (Phase 2)

- Données converties en embeddings (question + exemples + reponse)
- Index FAISS pour la recherche sémantique
- Métadonnées (`categorie`, `sources`, `version`) pour le contexte
- Filtrage par `valide` = true uniquement

## Tests et validation

### Tests automatisés

- Validation schéma JSON
- Tests de cohérence
- Vérification des URLs
- Contrôle de la qualité linguistique

### Tests manuels

- Tests utilisateur
- Validation des réponses
- Contrôle de l'exactitude
