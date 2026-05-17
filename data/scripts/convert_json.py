# convert_to_phase2.py
import json
from pathlib import Path

def convert(input_file: str, output_file: str):
    # Resolve path relative to this script's directory
    script_dir = Path(__file__).parent
    input_path = script_dir.parent / input_file if not Path(input_file).is_absolute() else input_file
    output_path = script_dir.parent / output_file if not Path(output_file).is_absolute() else output_file
    
    with open(input_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Gérer les deux structures possibles
    entries = data if isinstance(data, list) else data.get("questions_reponses", [])

    converted = []
    for i, item in enumerate(entries, 1):
        converted.append({
            "id": f"faq_{i:03d}",
            "categorie": item.get("categorie", "Général"),
            "sous_theme": item.get("categorie", "Général"),
            "question": item.get("question", ""),
            "reponse_enrichie": item.get("reponse", item.get("reponse_enrichie", "")),
            "exemples": item.get("exemples", [item.get("question", "")]),
            "sources": [item.get("etablissement", "SUP'PTIC")],
            "valide": True
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(converted)} entrées converties → {output_path}")

# Usage - use correct filename with hyphens and path
convert("json/drafts/theme3-transport-accesibilite.json", "json/faq3_converti_phase2.json")
