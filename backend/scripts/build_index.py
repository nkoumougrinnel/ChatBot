"""
build_index.py — Construction de l'index FAISS depuis les fichiers JSON v2.

Usage :
    python build_index.py
    python build_index.py --data-dir ../data --output-dir ../backend/rag_data

Ce script :
    1. Lit tous les fichiers JSON v2 du dossier data/
    2. Extrait les champs 'exemples' de chaque entrée
    3. Vectorise chaque exemple avec MiniLM
    4. Construit index.bin (index FAISS)
    5. Écrit metadata.json (mapping vecteur_id ↔ réponse)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import faiss
import numpy as np

# Chemin vers le module engine (pour import depuis scripts/)
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR/"chatbot"/"engine"))
from embedder import encode_batch, get_dimension


# -------------------------------------------------------------------
# Constantes
# -------------------------------------------------------------------
DEFAULT_DATA_DIR = _BACKEND_DIR.parent / "data"
DEFAULT_OUTPUT_DIR = _BACKEND_DIR / "rag_data"


def load_json_files(data_dir: Path) -> list[dict]:
    """
    Charge toutes les entrées FAQ depuis les fichiers JSON v2 du dossier data/.

    Seules les entrées avec "valide": true sont incluses.

    Returns:
        Liste de dicts (entrées FAQ valides).
    """
    entries = []
    json_files = sorted(data_dir.glob("faq_*.json"))

    if not json_files:
        print(f"[build_index] AVERTISSEMENT : aucun fichier faq_*.json trouvé dans '{data_dir}'")
        # Inclure tous les .json comme fallback
        json_files = sorted(data_dir.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[build_index]   ERREUR lecture '{json_file.name}' : {e}")
            continue

        items = data if isinstance(data, list) else [data]
        file_count = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            # Ignorer les entrées non validées
            if item.get("valide") is False:
                continue

            question = item.get("question", "")
            answer = item.get("reponse_enrichie", item.get("answer", item.get("response", "")))
            examples = item.get("exemples", item.get("examples", []))
            categorie = item.get("categorie", "Général")
            source = item.get("sources", [])
            source_str = ", ".join(source) if isinstance(source, list) else str(source)
            intent = item.get("id", f"faq_{len(entries)}")

            if not question or not answer:
                continue

            # L'entrée principale est aussi un "exemple"
            all_examples = [question] + [
                ex for ex in examples if isinstance(ex, str) and ex.strip()
            ]
            # Dédoublonner
            seen = set()
            unique_examples = []
            for ex in all_examples:
                key = ex.strip().lower()
                if key not in seen:
                    seen.add(key)
                    unique_examples.append(ex.strip())

            entries.append({
                "intent": intent,
                "question": question,
                "answer": answer,
                "examples": unique_examples,
                "categorie": categorie,
                "source": source_str,
            })
            file_count += 1

        print(f"[build_index]   {json_file.name} : {file_count} entrées chargées")

    return entries


def build_index(entries: list[dict], output_dir: Path) -> tuple[int, int]:
    """
    Vectorise les exemples et construit l'index FAISS + metadata.json.

    Args:
        entries:    Liste d'entrées FAQ (chargées par load_json_files).
        output_dir: Dossier de sortie pour index.bin et metadata.json.

    Returns:
        Tuple (nb_vecteurs, nb_entrees) pour le rapport.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.bin"
    metadata_path = output_dir / "metadata.json"

    dim = get_dimension()  # 384 pour MiniLM

    # --- Collecte de tous les textes à vectoriser ---
    all_texts = []
    all_meta = []

    for entry in entries:
        for example in entry["examples"]:
            all_texts.append(example)
            all_meta.append({
                "vecteur_id": len(all_texts) - 1,
                "intent": entry["intent"],
                "example": example,
                "response": entry["answer"],
                "categorie": entry["categorie"],
                "source": entry["source"],
            })

    if not all_texts:
        print("[build_index] ERREUR : aucun texte à vectoriser.")
        return 0, 0

    print(f"\n[build_index] Vectorisation de {len(all_texts)} exemples avec MiniLM...")
    t0 = time.time()
    vectors = encode_batch(all_texts)  # shape (N, 384), float32, normalisés
    elapsed = time.time() - t0
    print(f"[build_index] Vectorisation terminée : {len(all_texts)} vecteurs en {elapsed:.1f}s "
          f"({elapsed / len(all_texts) * 1000:.1f} ms/vecteur)")

    # --- Construction index FAISS (IndexFlatIP = produit interne sur vecteurs normalisés) ---
    print(f"[build_index] Construction de l'index FAISS (IndexFlatIP, dim={dim})...")
    index = faiss.IndexFlatIP(dim)  # Inner Product = cosine sim sur vecteurs normalisés
    index.add(vectors)
    print(f"[build_index] Index FAISS construit : {index.ntotal} vecteurs")

    # --- Sauvegarde ---
    faiss.write_index(index, str(index_path))
    print(f"[build_index] index.bin sauvegardé : '{index_path}'")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)
    print(f"[build_index] metadata.json sauvegardé : '{metadata_path}' ({len(all_meta)} entrées)")

    return len(all_texts), len(entries)


def quick_test(output_dir: Path, n_tests: int = 5) -> None:
    """Effectue un test rapide de l'index construit."""
    index_path = output_dir / "index.bin"
    metadata_path = output_dir / "metadata.json"

    if not index_path.exists():
        return

    print("\n[build_index] === Test de l'index ===")
    index = faiss.read_index(str(index_path))
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    from embedder import encode

    test_questions = [
        "C'est combien pour s'inscrire ?",
        "Quels sont les frais de scolarité ?",
        "Comment rejoindre le club informatique ?",
        "Quelles sont les filières disponibles ?",
        "Quel temps fait-il ?",  # hors domaine
    ][:n_tests]

    for q in test_questions:
        vec = encode(q)
        vec_2d = np.expand_dims(vec, axis=0)
        distances, indices = index.search(vec_2d, 3)

        print(f"\nQ : '{q}'")
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = metadata[idx]
            print(f"  → score={dist:.4f} | [{meta['categorie']}] {meta['example'][:55]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction de l'index FAISS pour SUP'ONE Phase 2")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help=f"Dossier contenant les fichiers JSON (défaut : {DEFAULT_DATA_DIR})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f"Dossier de sortie (défaut : {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--no-test", action="store_true", help="Ne pas lancer le test post-build")
    args = parser.parse_args()

    print("=" * 60)
    print("  build_index.py — ChatBot SUP'ONE Phase 2")
    print("=" * 60)
    print(f"  Dossier données : {args.data_dir}")
    print(f"  Dossier sortie  : {args.output_dir}\n")

    t_total = time.time()

    # 1. Charger les JSON
    print("[build_index] Chargement des fichiers JSON...")
    entries = load_json_files(args.data_dir)
    if not entries:
        print("[build_index] ERREUR : aucune entrée chargée. Vérifiez le dossier data/.")
        sys.exit(1)
    print(f"[build_index] Total : {len(entries)} entrées FAQ valides chargées\n")

    # 2. Construire l'index
    nb_vectors, nb_entries = build_index(entries, args.output_dir)

    elapsed_total = time.time() - t_total
    print(f"\n[build_index] ✔ Index construit en {elapsed_total:.1f}s")
    print(f"  {nb_vectors} vecteurs issus de {nb_entries} entrées FAQ")

    # 3. Test rapide
    if not args.no_test:
        quick_test(args.output_dir)

    print("\n[build_index] Terminé. L'index est prêt.")


if __name__ == "__main__":
    main()
