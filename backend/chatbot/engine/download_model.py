from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Modèle sauvegardé dans : {model.model_card_data}")