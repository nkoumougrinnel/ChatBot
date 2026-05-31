import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ID_PATTERN = re.compile(r"^faq_\d{3}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+$")

REQUIRED_FIELDS = {
    "id": str,
    "categorie": str,
    "sous_theme": str,
    "question": str,
    "reponse_enrichie": str,
    "exemples": list,
    "sources": list,
    "date_creation": str,
    "version": str,
    "valide": bool,
}


def validate_item(item, index):
    errors = []

    if not isinstance(item, dict):
        return [f"Entrée {index} : doit être un objet JSON."]

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in item:
            errors.append(f"Entrée {index} : champ manquant '{field}'.")
            continue
        value = item[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"Entrée {index} : champ '{field}' doit être de type {expected_type.__name__}, trouvé {type(value).__name__}."
            )

    if "id" in item and isinstance(item.get("id"), str):
        if not ID_PATTERN.match(item["id"]):
            errors.append(
                f"Entrée {index} : id '{item['id']}' invalide. Utiliser le format faq_001 à faq_999."
            )

    if "date_creation" in item and isinstance(item.get("date_creation"), str):
        date_value = item["date_creation"]
        if not DATE_PATTERN.match(date_value):
            errors.append(
                f"Entrée {index} : date_creation '{date_value}' doit être au format YYYY-MM-DD."
            )
        else:
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    f"Entrée {index} : date_creation '{date_value}' n'est pas une date valide."
                )

    if "version" in item and isinstance(item.get("version"), str):
        if not VERSION_PATTERN.match(item["version"]):
            errors.append(
                f"Entrée {index} : version '{item['version']}' doit être au format majeur.mineur (ex. 2.0)."
            )

    if "exemples" in item and isinstance(item.get("exemples"), list):
        if not item["exemples"]:
            errors.append(f"Entrée {index} : la liste 'exemples' ne doit pas être vide.")
        elif any(not isinstance(example, str) or not example.strip() for example in item["exemples"]):
            errors.append(f"Entrée {index} : chaque exemple doit être une chaîne non vide.")

    if "sources" in item and isinstance(item.get("sources"), list):
        if not item["sources"]:
            errors.append(f"Entrée {index} : la liste 'sources' ne doit pas être vide.")
        elif any(not isinstance(source, str) or not source.strip() for source in item["sources"]):
            errors.append(f"Entrée {index} : chaque source doit être une chaîne non vide.")

    return errors


def load_json_file(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERREUR : le fichier '{path}' est introuvable.")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"ERREUR : le fichier '{path}' n'est pas un JSON valide : {exc}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Valide la conformité d'un fichier JSON FAQ.")
    parser.add_argument("file", help="Chemin du fichier JSON à vérifier")
    args = parser.parse_args()

    file_path = Path(args.file)
    data = load_json_file(file_path)

    if not isinstance(data, list):
        print(f"ERREUR : le fichier JSON doit contenir une liste d'objets.")
        sys.exit(1)

    errors = []
    categories = {}
    valid_count = 0

    for idx, item in enumerate(data, start=1):
        item_errors = validate_item(item, idx)
        if item_errors:
            errors.extend(item_errors)
        else:
            valid_count += 1
            categorie = item.get("categorie")
            if isinstance(categorie, str):
                categories[categorie] = categories.get(categorie, 0) + 1

    if errors:
        print(f"Validation échouée pour {file_path.name} : {len(errors)} erreur(s) trouvée(s).")
        for error in errors[:100]:
            print(f"- {error}")
        if len(errors) > 100:
            print(f"... et {len(errors) - 100} autres erreurs.")
        sys.exit(1)

    total = len(data)
    print(f"Validation réussie pour {file_path.name}")
    print(f"{total} FAQs analysées")
    print(f"{valid_count} FAQs valides")
    if categories:
        main_category = max(categories, key=categories.get)
        print(f"Catégorie principale : {main_category} ({categories[main_category]} FAQs)")

    sys.exit(0)


if __name__ == "__main__":
    main()
