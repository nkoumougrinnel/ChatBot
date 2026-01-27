#!/usr/bin/env python3
"""
Script de reset et réimport des données.
- Supprime la base de données
- Déplace les fichiers archivés vers validated
- Réimporte les données
"""

import os
import shutil
from pathlib import Path
import subprocess
import sys

def reset_and_import():
    root = Path(__file__).resolve().parent.parent.parent
    phase1_root = Path(__file__).resolve().parent.parent

    # 1. Supprimer la DB
    db_path = root / "db" / "faq.db"
    if db_path.exists():
        db_path.unlink()
        print("Base de données supprimée.")

    # 2. Déplacer archived vers validated
    archived_dir = phase1_root / "data" / "archived"
    validated_dir = phase1_root / "data" / "validated"
    validated_dir.mkdir(parents=True, exist_ok=True)

    moved = 0
    for file in archived_dir.glob("*.csv"):
        shutil.move(str(file), str(validated_dir / file.name))
        moved += 1

    if moved > 0:
        print(f"{moved} fichier(s) déplacé(s) de archived vers validated.")

    # 3. Lancer l'import
    script_dir = phase1_root / "scripts"
    result = subprocess.run([sys.executable, "import_validated.py"], cwd=str(script_dir), capture_output=True, text=True)

    if result.returncode == 0:
        print("Import réussi.")
        print(result.stdout.strip())
    else:
        print("Erreur lors de l'import:")
        print(result.stderr)

if __name__ == "__main__":
    reset_and_import()
