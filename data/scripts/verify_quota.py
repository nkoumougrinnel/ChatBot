# verify_quota.py

import argparse
import json
import sys

parser = argparse.ArgumentParser(description="Vérifie le quota d'entrées valides dans un fichier JSON.")
parser.add_argument("--file", required=True, help="Chemin du fichier JSON à vérifier")
parser.add_argument("--quota", type=int, default=70, help="Quota minimum de questions répondues valides")
args = parser.parse_args()

with open(args.file, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    print(f"[verify_quota] ERREUR : le fichier {args.file} doit contenir une liste JSON.")
    sys.exit(1)

total = len(data)
valides = sum(1 for d in data if isinstance(d, dict) and d.get("valide") is True)
rejets = total - valides

print(f"[verify_quota] Fichier : {args.file}")
print(f" Total entrees : {total}")
print(f" Valides : {valides}")
print(f" Rejets : {rejets}")
print(f" Quota attendu : {args.quota}")

if valides < args.quota:
    print(f" ECHEC : {args.quota - valides} Q/R manquants !")
    sys.exit(1)
else:
    print(f" OK : quota atteint ({valides} >= {args.quota})")
    sys.exit(0)
