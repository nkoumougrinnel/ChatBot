"""
Construction de l'index FAISS (rag_data/index.bin + metadata.json) pour le pipeline Gen3.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
_DEFAULT_RAG_DIR = Path(os.environ.get("RAG_DATA_DIR", _BACKEND_DIR / "rag_data"))


def _default_json_sources() -> list[Path]:
    paths = [
        _REPO_ROOT / "data" / "supptic_chatbot_standard.json",
        _BACKEND_DIR / "data" / "json" / "supptic_chatbot_standard.json",
        _BACKEND_DIR / "data" / "json" / "bases.json",
    ]
    return [p for p in paths if p.is_file()]


def _load_supptic_intents(path: Path) -> list[dict]:
    """Format intent / examples / responses / metadata."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []

    entries: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        responses = item.get("responses") or item.get("response")
        if isinstance(responses, list):
            answer = (responses[0] or "").strip() if responses else ""
        else:
            answer = (responses or "").strip()
        if not answer:
            continue

        meta = item.get("metadata") or {}
        categorie = meta.get("categorie", "Général")
        source = meta.get("source", path.name)
        intent = item.get("intent", "")

        examples = item.get("examples") or item.get("example")
        if isinstance(examples, str):
            examples = [examples]
        if not examples:
            q = item.get("question", "").strip()
            if q:
                examples = [q]
        for ex in examples or []:
            if ex and isinstance(ex, str) and ex.strip():
                entries.append({
                    "example": ex.strip(),
                    "response": answer,
                    "categorie": categorie,
                    "source": source,
                    "intent": intent,
                })
    return entries


def _load_generic_json(path: Path) -> list[dict]:
    """Format liste {question, answer/reponse_enrichie, categorie}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("items", data.get("faqs", []))
    entries: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if "examples" in item and "responses" in item:
            entries.extend(_load_supptic_intents_from_item(item, path.name))
            continue
        question = (item.get("question") or "").strip()
        answer = (
            item.get("reponse_enrichie")
            or item.get("answer")
            or item.get("response")
            or ""
        ).strip()
        if question and answer:
            entries.append({
                "example": question,
                "response": answer,
                "categorie": item.get("categorie", "Général"),
                "source": path.name,
                "intent": item.get("intent", ""),
            })
    return entries


def _load_supptic_intents_from_item(item: dict, source_name: str) -> list[dict]:
    responses = item.get("responses") or []
    answer = (responses[0] or "").strip() if responses else ""
    if not answer:
        return []
    meta = item.get("metadata") or {}
    out = []
    for ex in item.get("examples") or []:
        if ex and isinstance(ex, str) and ex.strip():
            out.append({
                "example": ex.strip(),
                "response": answer,
                "categorie": meta.get("categorie", "Général"),
                "source": meta.get("source", source_name),
                "intent": item.get("intent", ""),
            })
    return out


def _load_json_file(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], dict)
        and "examples" in data[0]
        and ("responses" in data[0] or "response" in data[0])
    ):
        entries: list[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            responses = item.get("responses") or item.get("response")
            if isinstance(responses, list):
                answer = (responses[0] or "").strip() if responses else ""
            else:
                answer = (responses or "").strip()
            if not answer:
                continue
            meta = item.get("metadata") or {}
            for ex in item.get("examples") or []:
                if ex and isinstance(ex, str) and ex.strip():
                    entries.append({
                        "example": ex.strip(),
                        "response": answer,
                        "categorie": meta.get("categorie", "Général"),
                        "source": meta.get("source", path.name),
                        "intent": item.get("intent", ""),
                    })
        return entries
    return _load_generic_json(path)


def load_entries_from_json(paths: list[Path] | None = None) -> list[dict]:
    paths = paths or _default_json_sources()
    seen: set[tuple[str, str]] = set()
    entries: list[dict] = []

    for path in paths:
        if path.name == "conversational_rules.json":
            continue
        try:
            batch = _load_json_file(path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Ignorer %s : %s", path, exc)
            continue

        added = 0
        for e in batch:
            key = (e["example"].lower(), e["response"][:80])
            if key in seen:
                continue
            seen.add(key)
            entries.append(e)
            added += 1
        logger.info("Charge %s : +%d entrees uniques (total %d)", path.name, added, len(entries))

    return entries


def load_entries_from_django() -> list[dict]:
    try:
        from faq.models import FAQ
    except Exception:
        return []

    entries = []
    for faq in FAQ.objects.filter(is_active=True).select_related("category"):
        entries.append({
            "example": faq.question,
            "response": faq.answer,
            "categorie": faq.category.name if faq.category_id else "Général",
            "source": "django_faq",
            "intent": f"faq_{faq.id}",
        })
    return entries


def build_rag_index(
    *,
    rag_dir: Path | None = None,
    json_paths: list[Path] | None = None,
    include_django: bool = True,
    max_entries: int | None = None,
) -> dict:
    """
    Construit index.bin et metadata.json. Retourne des statistiques.
    """
    from chatbot.engine.embedder import encode_batch, get_dimension

    rag_dir = rag_dir or _DEFAULT_RAG_DIR
    rag_dir.mkdir(parents=True, exist_ok=True)
    index_path = rag_dir / "index.bin"
    metadata_path = rag_dir / "metadata.json"

    entries = load_entries_from_json(json_paths)
    if include_django:
        entries.extend(load_entries_from_django())

    if not entries:
        raise RuntimeError(
            "Aucune entree FAQ pour l'index RAG. Verifiez data/supptic_chatbot_standard.json"
        )

    if max_entries and len(entries) > max_entries:
        entries = entries[:max_entries]
        logger.info("Limite --max-entries=%d appliquee", max_entries)

    texts = [e["example"] for e in entries]
    logger.info("Vectorisation MiniLM de %d textes...", len(texts))
    vectors = encode_batch(texts, batch_size=64)
    dim = get_dimension()

    index = faiss.IndexFlatIP(dim)
    index.add(np.ascontiguousarray(vectors))

    faiss.write_index(index, str(index_path))
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=0)

    stats = {
        "vectors": index.ntotal,
        "dim": dim,
        "index_path": str(index_path),
        "metadata_path": str(metadata_path),
    }
    logger.info("Index FAISS ecrit : %s (%d vecteurs)", index_path, index.ntotal)
    return stats
