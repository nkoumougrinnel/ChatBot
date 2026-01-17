# Phase 1 : Guide d'Utilisation

## 🚀 Utilisation des Scripts

### 1. Synchronisation des données

Récupère les nouvelles données depuis Google Sheets et les place dans `phase-1/data/pending/`.

```bash
python phase-1/scripts/sync.py
```

#### Comportement

- ✅ Vérifie la connexion internet
- ✅ Récupère **uniquement les nouvelles données** depuis Google Sheets (via suivi d'index)
- ✅ Crée un fichier CSV horodaté dans `phase-1/data/pending/`
- ✅ Met à jour `phase-1/data/last_row.txt` avec le dernier index traité
- ✅ Log l'opération dans `logs/sync.log`

#### Format du fichier généré

```
new_data_2026-01-17_14-30.csv
```

Contenu :

```csv
question,answer
"Qu'est-ce que...?","Réponse..."
"Comment...?","Explication..."
```

### 2. Workflow de Validation

L'équipe valide manuellement les fichiers selon ce workflow :

```
pending/                    processing/                    validated/
├── new_data_2026-01-17.csv ──▶ new_data_2026-01-17.csv ──▶ new_data_2026-01-17.csv
│                           (correction)
```

#### Étapes manuelles

1. Fichier apparaît dans `phase-1/data/pending/`
2. Quelqu'un **déplace** le fichier vers `phase-1/data/processing/`
3. **Corriger** les données si nécessaire (ouvrir le CSV, modifier)
4. **Déplacer** vers `phase-1/data/validated/` quand prêt

### 3. Import des données validées

Lit les fichiers dans `phase-1/data/validated/`, les insère en base, puis les archive.

```bash
python phase-1/scripts/import_validated.py
```

#### Comportement

- ✅ Lit tous les fichiers CSV dans `phase-1/data/validated/`
- ✅ Insère les données dans `db/faq.db`
- ✅ Déplace les fichiers vers `phase-1/data/archived/`
- ✅ Log l'opération dans `logs/sync.log`

#### Résultat

```
validated/                        archived/
├── new_data_2026-01-17.csv ──▶ new_data_2026-01-17.csv
```

Les données sont maintenant dans `db/faq.db` ✅

### 4. Reset et Réimport Complet

⚠️ **À utiliser avec prudence** : Supprime la base de données et recommence à zéro.

```bash
python phase-1/scripts/reset_and_import.py
```

#### Comportement

- Supprime `db/faq.db`
- Remet les fichiers de `phase-1/data/archived/` vers `phase-1/data/validated/`
- Réimporte tous les fichiers
- Recrée la base de données vierge

## 📊 Vérifier les Données

### Afficher le contenu de la base

```bash
python phase-1/tests/test_db.py
```

### Vérifier les fichiers en attente

```bash
ls phase-1/data/pending/
ls phase-1/data/processing/
ls phase-1/data/validated/
ls phase-1/data/archived/
```

### Consulter les logs

```bash
tail -f logs/sync.log
```

## 🔄 Workflow Complet : Jour Type

```bash
# Matin : Récupérer les nouveaux fichiers
python phase-1/scripts/sync.py

# [Équipe valide les fichiers manuellement]

# Soir : Importer les fichiers validés
python phase-1/scripts/import_validated.py

# Vérifier que tout s'est bien passé
python phase-1/tests/test_db.py
```

## ⚙️ Troubleshooting

### Erreur : `Clé de service non trouvée`

```
FileNotFoundError: phase-1/config/faq-service-key.json
```

**Solution** : Voir [SETUP.md](SETUP.md) section "Configurer les clés d'accès"

### Erreur : `Permission denied on Google Sheets`

**Solution** :

1. Vérifier que la feuille est partagée avec l'email du compte de service
2. Vérifier que le SHEET_ID est correct

### Aucun fichier généré après sync.py

**Possible causes** :

- Pas de nouvelles données depuis le dernier import
- Vérifier `phase-1/data/last_row.txt`
- Consulter les logs : `tail logs/sync.log`

---

Pour la configuration complète : [SETUP.md](SETUP.md)  
Pour le README Phase 1 : [README.md](README.md)
