import json

def load_intents(file_path):
    """Charge les intents depuis un fichier JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        intents = json.load(f)
    return intents