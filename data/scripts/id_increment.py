import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description="Renumérote les IDs d'un fichier JSON FAQ.")
parser.add_argument("--file", required=True, help="Chemin du fichier JSON à modifier")
parser.add_argument("--start", type=int, required=True, help="Numéro de départ (ex: 1 pour faq_001)")
args = parser.parse_args()

file_path = Path(args.file)

if not file_path.exists():
    print(f"ERREUR : le fichier '{args.file}' est introuvable.")
    sys.exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    print("ERREUR : le fichier JSON doit contenir une liste d'objets.")
    sys.exit(1)

for i, item in enumerate(data):
    if isinstance(item, dict):
        item["id"] = f"faq_{args.start + i:03d}"

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"OK : {len(data)} IDs remplacés dans '{file_path.name}'")
print(f"     De faq_{args.start:03d} à faq_{args.start + len(data) - 1:03d}")
