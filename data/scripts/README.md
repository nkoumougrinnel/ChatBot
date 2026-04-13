# Scripts de traitement des données

Outils Python pour valider, analyser et maintenir le dataset FAQ.

## validate_json.py

Valide la conformité des fichiers JSON selon le schéma de données attendu.

### Utilisation

```bash
python validate_json.py [fichier.json]
```

### Vérifications effectuées

- Structure générale du JSON (liste d'objets)
- Présence des champs requis : `id`, `categorie`, `sous_theme`, `question`, `reponse_enrichie`, `exemples`, `sources`, `date_creation`, `version`, `valide`
- Types de données corrects
- Format des IDs (convention `faq_[001-999]`)
- Cohérence des métadonnées et sources
- Validation des dates et versions

### Exemple de sortie

```
Validation réussie pour faq_admissions.json
15 FAQs validées
Catégorie: Admissions
```

## verify_quota.py
## import_json.py

Importe un fichier JSON dans la base Django en ignorant les entrées déjà présentes selon l'identifiant JSON unique `id`.

### Utilisation

```bash
python import_json.py --file data/json/validated/Inscription_admissions--condition_admission.json
```

### Options

- `--dry-run`: simule l'import sans écrire en base

### Comportement

- lit un fichier JSON contenant une liste d'objets
- crée les catégories manquantes
- crée une FAQ par entrée
- ignore les doublons si un `id` JSON existe déjà en base

### Exemple de sortie

```
[DRY-RUN] Importer FAQ id=faq_001 question="Quels sont les critères académiques..."

Résumé de l import:
  Total Lignes : 25
  Importées : 25
  Ignorées (id dupliqué) : 0
  Erreurs : 0
```

## stats_dataset.py

Génère des statistiques complètes sur le dataset.

### Utilisation

```bash
python stats_dataset.py
```

### Métriques calculées

- **Quantitatives**
  - Nombre total de FAQs
  - Nombre total d'exemples alternatifs
  - Nombre moyen d'exemples par FAQ
  - Répartition par catégories et sous-thèmes
  - Taux de validation (`valide` = true)

- **Qualitatives**
  - Diversité des formulations dans `exemples`
  - Couverture des sources
  - Répartition temporelle (`date_creation`)
  - Versions des contenus

### Exemple de sortie

```
STATISTIQUES DU DATASET FAQ

Total FAQs: 127 (112 validées)
Total exemples alternatifs: 543
Moyenne exemples/FAQ: 4.3

REPARTITION PAR CATEGORIE:
- Admissions: 23 FAQs (20 validées)
- Formation: 34 FAQs (32 validées)
- Frais: 19 FAQs (18 validées)
- Vie étudiante: 28 FAQs (25 validées)
- Carrières: 19 FAQs (17 validées)

COUVERTURE TEMPORELLE:
- 2024: 45 FAQs
- 2025: 67 FAQs
- 2026: 15 FAQs

TAUX DE VALIDATION: 88.2%
```
