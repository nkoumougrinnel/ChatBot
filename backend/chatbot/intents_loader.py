"""
Chargement des intents depuis un fichier JSON.
"""

import json
import os


def load_intents(file_path: str) -> list:
    """
    Charge les intents depuis un fichier JSON.

    Args:
        file_path (str): Chemin absolu ou relatif vers le fichier JSON.

    Returns:
        list: Liste des intents chargés.

    Raises:
        FileNotFoundError: Si le fichier est introuvable.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier d'intents introuvable : {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        intents = json.load(f)
    return intents
