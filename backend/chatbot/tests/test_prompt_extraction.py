# test_prompt_extraction.py
import sys
sys.path.insert(0, 'backend')

from chatbot.engine.faiss_search import search_with_metadata, load_index
from chatbot.engine.embedder import encode
from chatbot.engine.prompt_builder import build_prompt

# Charger index
load_index()

# Question d'exemple
question = "Comment sont regroupées les matières ?"
vec = encode(question)
contexts = search_with_metadata(vec, k=3)

# Construire le prompt
prompt = build_prompt(question, contexts)

print(f"Longueur du prompt : {len(prompt)}")
print("\n=== PROMPT COMPLET ===\n")
print(prompt)

# Copier ce prompt dans Postman pour tester