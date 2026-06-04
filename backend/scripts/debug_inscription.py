import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

import numpy as np

from chatbot.engine.coherence import lexical_overlap, resolve_kb_answer
from chatbot.engine.embedder import encode
from chatbot.engine.faiss_search import search_with_metadata
from chatbot.engine.tfidf_fallback import search_top_k

q = "Comment s'inscrire à SUP'PTIC ?"
vec = np.array(encode(q), dtype=np.float32)
ctx = search_with_metadata(vec, k=3)
print("FAISS top:")
for c in ctx[:3]:
    ex = c.get("example", "")
    print(f"  {c['score']:.3f} overlap={lexical_overlap(q, ex):.3f} | {ex[:75]}")
print("TF-IDF top:")
for h in search_top_k(q, k=3):
    rq = h.get("question", "")
    print(f"  {h['score']:.3f} overlap={lexical_overlap(q, rq):.3f} | {rq[:75]}")
pick = resolve_kb_answer(q, ctx)
print("PICK:", pick)
