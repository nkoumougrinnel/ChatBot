import sqlite3
from pathlib import Path

def test_db_queries():
    """Test script pour interroger la base de données FAQ."""

    # Chemin vers la DB
    db_path = Path(__file__).resolve().parent.parent / "db" / "faq.db"

    if not db_path.exists():
        print(f"Base de données introuvable: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Vérifier la structure de la table
        cursor.execute("PRAGMA table_info(faq)")
        columns = cursor.fetchall()
        print("Structure de la table faq:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # Compter le nombre total d'entrées
        cursor.execute("SELECT COUNT(*) FROM faq")
        count = cursor.fetchone()[0]
        print(f"\nNombre total d'entrées: {count}")

        # Afficher les 5 premières entrées
        cursor.execute("SELECT id, question, answer FROM faq LIMIT 5")
        rows = cursor.fetchall()
        print("\nPremières entrées:")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"Question: {row[1] or 'N/A'}")
            answer = row[2] or 'N/A'
            print(f"Réponse: {answer[:100]}..." if len(answer) > 100 else f"Réponse: {answer}")
            print("-" * 50)

        # Recherche par mot-clé (exemple)
        keyword = input("\nEntrez un mot-clé pour la recherche: ")
        cursor.execute("SELECT id, question, answer FROM faq WHERE question LIKE ? OR answer LIKE ?", (f'%{keyword}%', f'%{keyword}%'))
        results = cursor.fetchall()
        print(f"\nRésultats pour '{keyword}': {len(results)} trouvés")
        for row in results[:3]:  # Afficher max 3
            print(f"ID: {row[0]} - Question: {row[1][:50]}...")

    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
    finally:
        conn.rollback()  # Annuler l'insertion de test
        conn.close()

if __name__ == "__main__":
    test_db_queries()