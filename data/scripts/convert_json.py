# convert_to_phase2.py
import json
from pathlib import Path

def convert(input_file: str, output_file: str):
    with open(input_file, "r", encoding="utf-8-sig") as f:
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

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(converted)} entrées converties → {output_file}")
# Usage
convert("theme3_transport_accessibilite.json", "faq3_converti_phase2.json")
