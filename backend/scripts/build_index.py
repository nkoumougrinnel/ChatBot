"""
build_index.py — Construction de l'index FAISS depuis les données FAQ JSON ou SQLite.
Génération 3 : déduplication cross-fichiers, sauvegarde atomique, batch_size configurable.

Usage :
    python build_index.py
    python build_index.py --data-dir ../data/json/validated --output-dir ../backend/rag_data
    python build_index.py --source sqlite --sqlite-db ../backend/db.sqlite3
    python build_index.py --no-test --batch-size 128

Ce script :
    1. Lit les fichiers JSON validés du dossier data/ ou la base SQLite
    2. Extrait les champs 'id', 'question', 'reponse_enrichie', 'exemples', 'categorie'
    3. Déduplique globalement les questions (cross-fichiers)
    4. Vectorise chaque texte avec MiniLM (batch configurable)
    5. Construit index.bin (index FAISS) — sauvegarde atomique
    6. Écrit metadata.json (mapping vecteur_id ↔ réponse) — sauvegarde atomique
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

import faiss
import numpy as np

_SCRIPT_DIR  = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
_REPO_ROOT   = _BACKEND_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR / "chatbot" / "engine"))

from embedder import encode_batch, get_dimension, encode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Chemins par défaut
# -------------------------------------------------------------------
DEFAULT_DATA_DIR   = _REPO_ROOT / "data" / "json" / "validated"
DEFAULT_OUTPUT_DIR = _BACKEND_DIR / "rag_data"
DEFAULT_SQLITE_DB  = _BACKEND_DIR / "db.sqlite3"
DEFAULT_SOURCE     = "json"


def _resolve_path(path: Path, fallback_bases: list[Path]) -> Path:
    if path.is_absolute():
        return path
    for base in fallback_bases:
        candidate = (base / path).resolve()
        if candidate.exists():
            return candidate
    return path


# -------------------------------------------------------------------
# Chargement JSON
# -------------------------------------------------------------------
def load_json_files(data_dir: Path) -> list[dict]:
    """
    Charge toutes les entrées FAQ depuis les fichiers JSON.

    Gen3 :
    - Déduplication globale cross-fichiers (seen_questions)
    - Rapport d'anomalies par fichier
    - Support formats v1 (answer) et v2 (reponse_enrichie)
    """
    entries: list[dict] = []
    seen_questions: set[str] = set()   # Gen3 — déduplication cross-fichiers
    stats = {"files": 0, "loaded": 0, "skipped_invalid": 0, "skipped_dup": 0}

    json_files = sorted(data_dir.glob("faq_*.json"))
    if not json_files:
        logger.warning("Aucun faq_*.json dans '%s' — fallback sur *.json", data_dir)
        json_files = sorted(data_dir.glob("*.json"))

    for json_file in json_files:
        stats["files"] += 1
        try:
            with open(json_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Erreur lecture '%s' : %s", json_file.name, e)
            continue

        items = data if isinstance(data, list) else [data]
        file_loaded = 0

        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("valide") is False:
                stats["skipped_invalid"] += 1
                continue

            question  = _text(item.get("question") or item.get("Question"))
            answer    = _text(
                item.get("reponse_enrichie") or item.get("reponse")
                or item.get("answer") or item.get("response")
            )
            examples  = item.get("exemples", item.get("examples", []))
            categorie = _text(item.get("categorie") or item.get("category")) or "Général"
            source    = item.get("sources", item.get("source", []))
            source_str = ", ".join(source) if isinstance(source, list) else str(source or "")
            faq_id    = _text(item.get("id") or item.get("intent")) or f"faq_{len(entries)}"

            if not question or not answer:
                stats["skipped_invalid"] += 1
                continue

            # Gen3 — déduplication cross-fichiers
            q_key = question.lower()
            if q_key in seen_questions:
                stats["skipped_dup"] += 1
                continue
            seen_questions.add(q_key)

            unique_examples = _dedup([question] + [
                ex.strip() for ex in examples
                if isinstance(ex, str) and ex.strip()
            ])

            entries.append({
                "intent":    faq_id,
                "question":  question,
                "answer":    answer,
                "examples":  unique_examples,
                "categorie": categorie,
                "source":    source_str,
            })
            file_loaded += 1

        stats["loaded"] += file_loaded
        logger.info("  %-40s : %d entrées", json_file.name, file_loaded)

    logger.info(
        "Bilan JSON : %d valides | %d invalides | %d doublons (sur %d fichiers)",
        stats["loaded"], stats["skipped_invalid"], stats["skipped_dup"], stats["files"],
    )
    return entries


# -------------------------------------------------------------------
# Chargement SQLite
# -------------------------------------------------------------------
def load_sqlite_entries(sqlite_db: Path) -> list[dict]:
    """Charge les entrées FAQ depuis une base SQLite Django."""
    entries: list[dict] = []
    seen_questions: set[str] = set()   # Gen3 — déduplication

    if not sqlite_db.exists():
        logger.error("Fichier SQLite non trouvé : %s", sqlite_db)
        return entries

    query = (
        "SELECT f.id, f.question, f.answer, f.source, c.name AS category "
        "FROM faq_faq f "
        "LEFT JOIN faq_category c ON f.category_id = c.id "
        "WHERE f.is_active = 1"
    )
    try:
        with sqlite3.connect(sqlite_db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()
    except sqlite3.Error as exc:
        logger.error("Erreur SQLite : %s", exc)
        return entries

    for row in rows:
        question = _text(row["question"])
        answer   = _text(row["answer"])
        if not question or not answer:
            continue

        q_key = question.lower()
        if q_key in seen_questions:
            continue
        seen_questions.add(q_key)

        source_str = _text(row["source"]) or ""
        entries.append({
            "intent":    f"faq_sqlite_{row['id']}",
            "question":  question,
            "answer":    answer,
            "examples":  _dedup([question]),
            "categorie": _text(row["category"]) or "Général",
            "source":    source_str,
        })

    logger.info("%d entrées lues depuis SQLite : %s", len(entries), sqlite_db)
    return entries


# -------------------------------------------------------------------
# Construction de l'index
# -------------------------------------------------------------------
def build_index(
    entries:    list[dict],
    output_dir: Path,
    batch_size: int = 64,    # Gen3 — batch configurable
) -> tuple[int, int]:
    """
    Vectorise les exemples et construit index.bin + metadata.json.

    Gen3 :
    - batch_size configurable (--batch-size)
    - Sauvegarde atomique (.tmp → rename) pour éviter un index corrompu
      si le processus est interrompu en cours d'écriture.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path    = output_dir / "index.bin"
    metadata_path = output_dir / "metadata.json"
    tmp_index     = output_dir / "index.bin.tmp"      # Gen3 — atomique
    tmp_meta      = output_dir / "metadata.json.tmp"  # Gen3 — atomique

    dim = get_dimension()

    # Collecte de tous les textes
    all_texts: list[str] = []
    all_meta:  list[dict] = []

    for entry in entries:
        for example in entry["examples"]:
            all_texts.append(example)
            all_meta.append({
                "vecteur_id": len(all_texts) - 1,
                "intent":     entry["intent"],
                "example":    example,
                "response":   entry["answer"],
                "categorie":  entry["categorie"],
                "source":     entry["source"],
            })

    if not all_texts:
        logger.error("Aucun texte à vectoriser — vérifiez votre source.")
        return 0, 0

    logger.info("Vectorisation de %d exemples (batch=%d)...", len(all_texts), batch_size)
    t0 = time.time()
    vectors = encode_batch(all_texts, batch_size=batch_size)   # Gen3 — batch_size
    elapsed = time.time() - t0
    logger.info(
        "Vectorisation terminée : %d vecteurs en %.1fs (%.1f ms/vecteur)",
        len(all_texts), elapsed, elapsed / len(all_texts) * 1000,
    )

    # Construction index FAISS
    logger.info("Construction IndexFlatIP (dim=%d)...", dim)
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    logger.info("Index FAISS : %d vecteurs", index.ntotal)

    # Sauvegarde atomique — Gen3
    faiss.write_index(index, str(tmp_index))
    tmp_index.rename(index_path)
    logger.info("index.bin sauvegardé : '%s'", index_path)

    with open(tmp_meta, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)
    tmp_meta.rename(metadata_path)
    logger.info("metadata.json sauvegardé : %d entrées", len(all_meta))

    return len(all_texts), len(entries)


# -------------------------------------------------------------------
# Test post-build
# -------------------------------------------------------------------
def quick_test(output_dir: Path, n_tests: int = 5) -> None:
    index_path    = output_dir / "index.bin"
    metadata_path = output_dir / "metadata.json"
    if not index_path.exists():
        return

    logger.info("=== Test de l'index ===")
    index = faiss.read_index(str(index_path))
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    test_questions = [
        "Comment intégrer SUP'PTIC ?",
        "Quels sont les frais de scolarité ?",
        "Quelles sont les filières disponibles ?",
        "Comment rejoindre le club informatique ?",
        "Quel temps fait-il ?",              # hors domaine attendu
    ][:n_tests]

    for q in test_questions:
        vec   = encode(q)
        vec2d = np.expand_dims(vec, axis=0)
        dists, indices = index.search(vec2d, 3)
        logger.info("Q : '%s'", q)
        for dist, idx in zip(dists[0], indices[0]):
            if idx == -1:
                continue
            meta  = metadata[idx]
            label = "DIRECT" if dist >= 0.55 else ("LLM" if dist >= 0.30 else "OFFBASE")
            logger.info(
                "  [%s] score=%.4f | [%s] %s",
                label, dist, meta["categorie"], meta["example"][:55],
            )


# -------------------------------------------------------------------
# Utilitaires
# -------------------------------------------------------------------
def _text(value) -> str:
    if not value:
        return ""
    return str(value).strip()


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# -------------------------------------------------------------------
# Point d'entrée
# -------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construction de l'index FAISS pour SUP'ONE Génération 3"
    )
    parser.add_argument("--source", choices=["json", "sqlite"], default=DEFAULT_SOURCE)
    parser.add_argument("--data-dir",   type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--sqlite-db",  type=Path, default=DEFAULT_SQLITE_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-size", type=int,  default=64,
                        help="Taille de batch MiniLM (défaut : 64)")
    parser.add_argument("--no-test", action="store_true")
    args = parser.parse_args()

    bases = [_REPO_ROOT, _BACKEND_DIR, _SCRIPT_DIR]
    args.data_dir   = _resolve_path(args.data_dir,   bases)
    args.sqlite_db  = _resolve_path(args.sqlite_db,  bases)
    args.output_dir = _resolve_path(args.output_dir, bases)

    print("=" * 60)
    print("  build_index.py — SUP'ONE Génération 3")
    print("=" * 60)
    logger.info("Source        : %s", args.source)
    logger.info("Dossier sortie : %s", args.output_dir)
    logger.info("Batch size    : %d", args.batch_size)

    t_total = time.time()

    if args.source == "sqlite":
        entries = load_sqlite_entries(args.sqlite_db)
    else:
        entries = load_json_files(args.data_dir)

    if not entries:
        logger.error("Aucune entrée chargée — vérifiez votre source.")
        sys.exit(1)

    logger.info("Total : %d entrées FAQ valides\n", len(entries))
    nb_vectors, nb_entries = build_index(entries, args.output_dir, args.batch_size)

    logger.info(
        "Index construit en %.1fs | %d vecteurs | %d entrées",
        time.time() - t_total, nb_vectors, nb_entries,
    )

    if not args.no_test:
        quick_test(args.output_dir)

    logger.info("Terminé. L'index est prêt pour la Génération 3.")


if __name__ == "__main__":
    main()
