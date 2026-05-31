"""
build_index.py — Construction de l'index FAISS depuis les données FAQ JSON ou SQLite.

Usage :
    python build_index.py
    python build_index.py --data-dir ../data/json/validated --output-dir ../backend/rag_data
    python build_index.py --source sqlite --sqlite-db ../backend/db.sqlite3

Ce script :
    1. Lit les fichiers JSON validés du dossier data/ ou la base SQLite
    2. Extrait les champs 'id', 'question', 'reponse_enrichie', 'exemples', 'categorie'
    3. Vectorise chaque texte avec MiniLM
    4. Construit index.bin (index FAISS)
    5. Écrit metadata.json (mapping vecteur_id ↔ réponse)
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import faiss
import numpy as np

# Chemin vers le module engine (pour import depuis scripts/)
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
_REPO_ROOT = _BACKEND_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR / "chatbot" / "engine"))
from embedder import encode_batch, get_dimension


# -------------------------------------------------------------------
# Constantes
# -------------------------------------------------------------------
DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "json" / "validated"
DEFAULT_OUTPUT_DIR = _BACKEND_DIR / "rag_data"
DEFAULT_SQLITE_DB = _BACKEND_DIR / "db.sqlite3"
DEFAULT_SOURCE = "json"


def _resolve_path(path: Path, fallback_bases: list[Path]) -> Path:
    """Résout un chemin relatif via plusieurs bases utiles."""
    if path.is_absolute():
        return path

    candidates = [path]
    for base in fallback_bases:
        candidates.append((base / path).resolve())

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return path


def load_json_files(data_dir: Path) -> list[dict]:
    """
    Charge toutes les entrées FAQ depuis les fichiers JSON du dossier data/.

    Le format valide suit le README de data/: chaque entrée doit contenir
    un champ 'id', 'question', 'reponse_enrichie', 'exemples' et 'categorie'.
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
            with open(json_file, "r", encoding="utf-8-sig") as f:
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

            question = item.get("question") or item.get("Question") or ""
            answer = item.get("reponse_enrichie") or item.get("reponse") or item.get("answer") or item.get("response") or ""
            examples = item.get("exemples", item.get("examples", []))
            categorie = item.get("categorie") or item.get("category") or "Général"
            source = item.get("sources", item.get("source", []))
            source_str = ", ".join(source) if isinstance(source, list) else str(source)
            faq_id = item.get("id") or item.get("intent") or f"faq_{len(entries)}"

            if not isinstance(question, str) or not isinstance(answer, str) or not isinstance(faq_id, str):
                continue

            question = question.strip()
            answer = answer.strip()
            faq_id = faq_id.strip()
            if not question or not answer or not faq_id:
                continue

            all_examples = [question] + [
                ex.strip() for ex in examples if isinstance(ex, str) and ex.strip()
            ]
            # Dédoublonner
            seen = set()
            unique_examples = []
            for ex in all_examples:
                key = ex.lower()
                if key not in seen:
                    seen.add(key)
                    unique_examples.append(ex)

            entries.append({
                "intent": faq_id,
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


def _normalize_source_value(source):
    if isinstance(source, list):
        return ", ".join(str(s) for s in source if s)
    if source is None:
        return ""
    return str(source)


def _normalize_text_value(value):
    if not value:
        return ""
    return str(value).strip()


def load_sqlite_entries(sqlite_db: Path) -> list[dict]:
    """Charge les entrées FAQ depuis une base SQLite."""
    entries = []

    if not sqlite_db.exists():
        print(f"[build_index] ERREUR : fichier SQLite non trouvé : {sqlite_db}")
        return entries

    query = (
        "SELECT f.id, f.question, f.answer, f.subtheme, f.source, c.name AS category "
        "FROM faq_faq f "
        "LEFT JOIN faq_category c ON f.category_id = c.id "
        "WHERE f.is_active = 1"
    )

    try:
        with sqlite3.connect(sqlite_db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()
    except sqlite3.Error as exc:
        print(f"[build_index] ERREUR SQLite : {exc}")
        return entries

    for row in rows:
        question = _normalize_text_value(row["question"])
        answer = _normalize_text_value(row["answer"])
        if not question or not answer:
            continue

        examples = [question]
        if row["source"]:
            examples.append(_normalize_text_value(row["source"]))

        category = _normalize_text_value(row["category"] or "Général")
        source = _normalize_source_value(row["source"])
        faq_id = f"faq_sqlite_{row['id']}"

        seen = set()
        unique_examples = []
        for ex in examples:
            key = ex.lower()
            if key not in seen:
                seen.add(key)
                unique_examples.append(ex)

        entries.append({
            "intent": faq_id,
            "question": question,
            "answer": answer,
            "examples": unique_examples,
            "categorie": category,
            "source": source,
        })

    print(f"[build_index]   {len(entries)} entrées lues depuis SQLite : {sqlite_db}")
    return entries


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
        # Admission
        "Comment intégrer SUP'PTIC ?",
        "Quels sont les frais de scolarité ?",
        # Filières
        "Quelles sont les filières disponibles ?",
        "C'est quoi la filière management ? ",
        # Vie pratique
        "Où se trouve SUP'PTIC ?",
        "Comment contacter l'administration ?",
        # Conversationnel
        "Bonjour, tu es qui ?",
        "Merci pour ton aide",
        # Carrières
        "Quels débouchés apres SUP'PTIC ?",
        "Comment rejoindre le club informatique ?",
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
    parser.add_argument("--source", choices=["json", "sqlite"], default=DEFAULT_SOURCE,
                        help="Source à indexer : json (par défaut) ou sqlite")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help=f"Dossier contenant les fichiers JSON (défaut : {DEFAULT_DATA_DIR})")
    parser.add_argument("--sqlite-db", type=Path, default=DEFAULT_SQLITE_DB,
                        help=f"Fichier SQLite à utiliser si --source sqlite (défaut : {DEFAULT_SQLITE_DB})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f"Dossier de sortie (défaut : {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--no-test", action="store_true", help="Ne pas lancer le test post-build")
    args = parser.parse_args()

    args.data_dir = _resolve_path(args.data_dir, [_REPO_ROOT, _BACKEND_DIR, _SCRIPT_DIR])
    args.sqlite_db = _resolve_path(args.sqlite_db, [_REPO_ROOT, _BACKEND_DIR, _SCRIPT_DIR])
    args.output_dir = _resolve_path(args.output_dir, [_REPO_ROOT, _BACKEND_DIR, _SCRIPT_DIR])

    print("=" * 60)
    print("  build_index.py — ChatBot SUP'ONE Phase 2")
    print("=" * 60)
    print(f"  Source         : {args.source}")
    print(f"  Dossier données : {args.data_dir if args.source == 'json' else args.sqlite_db}")
    print(f"  Dossier sortie  : {args.output_dir}\n")

    t_total = time.time()

    if args.source == "sqlite":
        print("[build_index] Chargement depuis SQLite...")
        entries = load_sqlite_entries(args.sqlite_db)
    else:
        print("[build_index] Chargement des fichiers JSON...")
        entries = load_json_files(args.data_dir)

    if not entries:
        print("[build_index] ERREUR : aucune entrée chargée. Vérifiez votre source de données.")
        sys.exit(1)
    print(f"[build_index] Total : {len(entries)} entrées FAQ valides chargées\n")

    nb_vectors, nb_entries = build_index(entries, args.output_dir)

    elapsed_total = time.time() - t_total
    print(f"\n[build_index] ✔ Index construit en {elapsed_total:.1f}s")
    print(f"  {nb_vectors} vecteurs issus de {nb_entries} entrées FAQ")

    if not args.no_test:
        quick_test(args.output_dir)

    print("\n[build_index] Terminé. L'index est prêt.")


if __name__ == "__main__":
    main()
