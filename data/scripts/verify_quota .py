# verify_quota.py
# Usage : python verify_quota.py--file faq_admissions_j1.json--quota
70
import json, argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True)
parser.add_argument("--quota", type=int, default=70)
args = parser.parse_args()
with open(args.file, "r", encoding="utf-8") as f:
data = json.load(f)
total = len(data)
valides = sum(1 for d in data if d.get("valide") is True)
rejets = total- valides
print(f"[verify_quota] Fichier : {args.file}")
print(f" Total entrees : {total}")
print(f" Valides : {valides}")
print(f" Rejets : {rejets}")
print(f" Quota attendu : {args.quota}")
if valides < args.quota:
print(f" ECHEC : {args.quota- valides} Q/R manquants !")
sys.exit(1)
else:
print(f" OK : quota atteint ({valides} >= {args.quota})")
sys.exit(0)