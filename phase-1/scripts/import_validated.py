import os
import sqlite3
import pandas as pd
import shutil
from pathlib import Path
import csv


def import_validated():
    # Chemins basés sur la racine du projet
    root = Path(__file__).resolve().parent.parent.parent
    db_path = root / "db" / "faq.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # S'assurer que la table existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )
    """)

    phase1_root = Path(__file__).resolve().parent.parent
    validated_dir = phase1_root / "data" / "validated"
    archived_dir = phase1_root / "data" / "archived"
    validated_dir.mkdir(parents=True, exist_ok=True)
    archived_dir.mkdir(parents=True, exist_ok=True)

    for file in os.listdir(validated_dir):
        if file.endswith(".csv"):
            filepath = validated_dir / file
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                rows = list(reader)

            # Insertion en BD
            for row in rows:
                question = row.get('Question', '').strip()
                answer = row.get('Réponse', '').strip()
                if question and answer:  # Skip empty rows
                    cursor.execute(
                        "INSERT INTO faq (question, answer) VALUES (?, ?)",
                        (question, answer),
                    )
            conn.commit()

            # Déplacement vers archived
            archived_path = archived_dir / file
            shutil.move(str(filepath), str(archived_path))
            print(f"{file} inséré en BD et archivé.")

    conn.close()


if __name__ == "__main__":
    import_validated()
