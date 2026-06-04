"""Diagnostic du pipeline RAG Gen3."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verifie que FAISS, TF-IDF fallback, embedder et Gemini sont operationnels."

    def handle(self, *args, **options):
        lines = []

        try:
            import faiss  # noqa: F401
            lines.append(("faiss-cpu", True, "OK"))
        except ImportError as e:
            lines.append(("faiss-cpu", False, str(e)))

        try:
            import sentence_transformers  # noqa: F401
            lines.append(("sentence-transformers", True, "OK"))
        except ImportError as e:
            lines.append(("sentence-transformers", False, str(e)))

        try:
            import google.generativeai  # noqa: F401
            lines.append(("google-generativeai", True, "OK"))
        except ImportError as e:
            lines.append(("google-generativeai", False, str(e)))

        from pathlib import Path
        rag = Path(__file__).resolve().parents[3] / "rag_data"
        idx = rag / "index.bin"
        meta = rag / "metadata.json"
        lines.append(("rag_data/index.bin", idx.exists(), str(idx)))
        lines.append(("rag_data/metadata.json", meta.exists(), str(meta)))

        try:
            from chatbot.engine import faiss_search, tfidf_fallback
            from chatbot.engine.embedder import encode
            import numpy as np

            faiss_search.load_index()
            fs = faiss_search.get_index_stats()
            lines.append(("FAISS charge", fs["loaded"], f"{fs['ntotal']} vecteurs"))

            tfidf_fallback.load()
            ts = tfidf_fallback.get_stats()
            lines.append(("TF-IDF fallback", ts["loaded"], f"{ts['entries_count']} entrees"))

            v = encode("test")
            lines.append(("Embedder MiniLM", bool(np.linalg.norm(v) > 0), f"shape={v.shape}"))

            from chatbot.engine.llm_client import check_availability
            llm = check_availability()
            lines.append(("Gemini API", llm["available"], llm.get("error") or llm.get("model", "")))

            from chatbot.engine.rag_pipeline import health
            h = health()
            lines.append(("Pipeline ready", h.get("ready", False), str(h)))
        except Exception as exc:
            lines.append(("Pipeline", False, f"{type(exc).__name__}: {exc}"))

        for name, ok, detail in lines:
            style = self.style.SUCCESS if ok else self.style.ERROR
            mark = "OK" if ok else "KO"
            self.stdout.write(style(f"  [{mark}] {name}: {detail}"))
