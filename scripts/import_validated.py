import os
import sqlite3
import pandas as pd
import shutil
from pathlib import Path


def import_validated():
    # Chemins basés sur la racine du projet
    root = Path(__file__).resolve().parent.parent
    db_path = root / "db" / "faq.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

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

    validated_dir = root / "data" / "validated"
    archived_dir = root / "data" / "archived"
    validated_dir.mkdir(parents=True, exist_ok=True)
    archived_dir.mkdir(parents=True, exist_ok=True)

    for file in os.listdir(validated_dir):
        if file.endswith(".csv"):
            filepath = validated_dir / file
            df = pd.read_csv(filepath)

            # Insertion en BD
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO faq (question, answer) VALUES (?, ?)",
                    (row.get('Question'), row.get('Réponse')),
                )
            conn.commit()

            # Déplacement vers archived
            archived_path = archived_dir / file
            shutil.move(str(filepath), str(archived_path))
            print(f"{file} inséré en BD et archivé.")

    conn.close()


if __name__ == "__main__":
    import_validated()
