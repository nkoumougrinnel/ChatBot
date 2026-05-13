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

Vérifie qu’un fichier JSON contient un nombre minimum d’entrées validées.

### Utilisation

```bash
python verify_quota.py --file faq_admissions_j1.json --quota 70
```

### Vérifications effectuées

- Lecture du fichier JSON
- Vérification que le contenu est une liste
- Comptage des objets avec `valide: true`
- Comparaison avec le quota demandé

### Exemple de sortie

```
[verify_quota] Fichier : faq_admissions_j1.json
 Total entrees : 75
 Valides : 72
 Rejets : 3
 Quota attendu : 70
 OK : quota atteint (72 >= 70)
```

## id_increment.py

Renumérote automatiquement les champs id des objets dans un fichier JSON FAQ selon la convention faq_[001-999].

### Utilisation

'''bash
python  id_increment.py --file faq_admissions.json --start 1
'''Options disponibles
--file : chemin du fichier JSON à modifier (obligatoire)

--start : numéro de départ pour la renumérotation (exemple : 1 → faq_001)

--output : chemin du fichier de sortie (optionnel, sinon le fichier original est écrasé)

### Vérifications effectuées

Existence du fichier fourni

Structure générale du JSON (liste d’objets)

Renumérotation séquentielle des IDs en respectant le format faq_XXX

Gestion des erreurs de parsing JSON

Possibilité de sauvegarder dans un fichier distinct

### Exemple de sortie

Code
OK : 75 IDs remplacés dans 'faq_admissions.json'
     De faq_001 à faq_075

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
