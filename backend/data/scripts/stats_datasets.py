import argparse
import json
import sys
from collections import Counter
from pathlib import Path


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


def collect_input_files(path: Path):
    if path.is_file():
        return [path]
    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if files:
            return files
        print(f"ERREUR : aucun fichier JSON trouvé dans le répertoire '{path}'.")
        sys.exit(1)
    print(f"ERREUR : le chemin '{path}' n'existe pas.")
    sys.exit(1)


def normalize_text(value):
    return str(value).strip()


def compute_statistics(items):
    total_faqs = len(items)
    valid_faqs = 0
    total_examples = 0
    unique_examples = set()
    unique_sources = set()
    categories = Counter()
    categories_valid = Counter()
    subthemes = Counter()
    years = Counter()
    versions = Counter()

    for item in items:
        if not isinstance(item, dict):
            continue
        valide = item.get("valide") is True
        if valide:
            valid_faqs += 1

        categorie = normalize_text(item.get("categorie", "Inconnue"))
        categories[categorie] += 1
        if valide:
            categories_valid[categorie] += 1

        sous_theme = normalize_text(item.get("sous_theme", "Inconnu"))
        subthemes[sous_theme] += 1

        exemple_list = item.get("exemples")
        if isinstance(exemple_list, list):
            total_examples += len(exemple_list)
            for exemple in exemple_list:
                if isinstance(exemple, str) and exemple.strip():
                    unique_examples.add(exemple.strip())

        sources_list = item.get("sources")
        if isinstance(sources_list, list):
            for source in sources_list:
                if isinstance(source, str) and source.strip():
                    unique_sources.add(source.strip())

        date_creation = item.get("date_creation")
        if isinstance(date_creation, str) and len(date_creation) >= 4:
            years[date_creation[:4]] += 1

        version = normalize_text(item.get("version", "inconnue"))
        versions[version] += 1

    average_examples = total_examples / total_faqs if total_faqs else 0.0
    validation_rate = (valid_faqs / total_faqs * 100) if total_faqs else 0.0

    return {
        "total_faqs": total_faqs,
        "valid_faqs": valid_faqs,
        "total_examples": total_examples,
        "average_examples": average_examples,
        "unique_examples": len(unique_examples),
        "unique_sources": len(unique_sources),
        "categories": categories,
        "categories_valid": categories_valid,
        "subthemes": subthemes,
        "years": years,
        "versions": versions,
        "validation_rate": validation_rate,
    }


def pretty_counter(counter, limit=None):
    items = counter.most_common(limit)
    return [f"- {key}: {value}" for key, value in items]


def main():
    default_dir = Path(__file__).resolve().parent.parent / "json" / "validated"
    if not default_dir.exists():
        default_dir = Path(__file__).resolve().parent.parent / "json"

    parser = argparse.ArgumentParser(description="Génère des statistiques complètes sur le dataset FAQ.")
    parser.add_argument(
        "--path",
        default=str(default_dir),
        help="Fichier JSON ou répertoire de fichiers JSON à analyser (par défaut: data/json/validated)",
    )
    args = parser.parse_args()

    input_path = Path(args.path)
    files = collect_input_files(input_path)

    all_items = []
    for file_path in files:
        data = load_json_file(file_path)
        if isinstance(data, list):
            all_items.extend(data)
        else:
            print(f"AVERTISSEMENT : le fichier '{file_path.name}' ne contient pas une liste d'objets JSON et sera ignoré.")

    if not all_items:
        print("ERREUR : aucun élément FAQ valide n'a été trouvé pour l'analyse.")
        sys.exit(1)

    stats = compute_statistics(all_items)

    print("STATISTIQUES DU DATASET FAQ\n")
    print(f"Total FAQs: {stats['total_faqs']} ({stats['valid_faqs']} validées)")
    print(f"Total exemples alternatifs: {stats['total_examples']}")
    print(f"Moyenne exemples/FAQ: {stats['average_examples']:.1f}")
    print(f"Formulations distinctes: {stats['unique_examples']}")
    print(f"Sources distinctes: {stats['unique_sources']}")

    print("\nREPARTITION PAR CATEGORIE:")
    for line in pretty_counter(stats["categories"]):
        category = line[2:]
        key = category.split(":", 1)[0]
        valid_count = stats["categories_valid"].get(key, 0)
        print(f"{line} ({valid_count} validées)")

    print("\nREPARTITION PAR SOUS-THEME:")
    for line in pretty_counter(stats["subthemes"], limit=15):
        print(line)

    if stats["years"]:
        print("\nCOUVERTURE TEMPORELLE:")
        for line in pretty_counter(stats["years"]):
            print(line)

    if stats["versions"]:
        print("\nVERSIONS DU CONTENU:")
        for line in pretty_counter(stats["versions"]):
            print(line)

    print(f"\nTAUX DE VALIDATION: {stats['validation_rate']:.1f}%")

    sys.exit(0)


if __name__ == "__main__":
    main()
