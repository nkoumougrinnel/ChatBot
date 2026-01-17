# Phase 1 : Installation et Configuration

## ✅ Prérequis

- Python 3.8+
- Accès à une feuille Google Sheets
- Clé de service Google (pour l'API Google Sheets)

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone <url_du_repo>
cd ChatBot
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les clés d'accès

#### Créer une clé de service Google

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet
3. Activer l'API Google Sheets
4. Créer une clé de service (JSON)
5. Télécharger le fichier JSON

#### Placer la clé

```bash
# Créer le dossier s'il n'existe pas
mkdir -p phase-1/config

# Placer le fichier
cp /chemin/vers/faq-service-key.json phase-1/config/
```

⚠️ **Important** : Ce fichier ne doit **jamais** être versionné (voir `.gitignore`)

### 4. Configurer la feuille Google Sheets

1. Créer une feuille Google Sheets
2. Ajouter les colonnes : `question` et `answer`
3. Partager la feuille avec l'email du compte de service
4. Récupérer l'ID de la feuille depuis l'URL : `https://docs.google.com/spreadsheets/d/SHEET_ID/`

### 5. Mettre à jour la configuration

Dans `phase-1/scripts/sync.py`, remplacer :

```python
SHEET_ID = "VOTRE_SHEET_ID_ICI"
```

## 🗂️ Structure des dossiers de données

La structure suivante sera créée automatiquement au premier lancement :

```
phase-1/data/
├── pending/     # Fichiers en attente de validation
├── processing/  # Fichiers en cours de traitement
├── validated/   # Fichiers validés et prêts à insérer
└── archived/    # Fichiers déjà traités (trace)
```

## 🗄️ Base de Données

### Initialisation

La base de données `db/faq.db` est créée automatiquement au premier import.

### Schéma

```sql
CREATE TABLE faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
);
```

### Test de la base

```bash
python phase-1/tests/test_db.py
```

## 📋 Vérification de l'installation

```bash
# 1. Vérifier les dépendances
pip list | grep -E "gspread|sqlite3"

# 2. Vérifier la structure
ls -la phase-1/config/
ls -la phase-1/data/

# 3. Tester la base de données
python phase-1/tests/test_db.py
```

## 🚀 Premier lancement

Voir le guide d'utilisation : [USAGE.md](USAGE.md)

---

Pour revenir au README Phase 1 : [README.md](README.md)
