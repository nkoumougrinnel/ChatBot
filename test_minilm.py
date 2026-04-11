from sentence_transformers import SentenceTransformer
print("Chargement du modele.....")
model= SentenceTransformer("all-MiniLM-L6-v2")

test="Quels sont les frais de scolarite a SUP'PTIC?"
vecteur= model.encode(test)
print(f"Modele charge")
print(f"Dimension du vecteur:{len(vecteur)}")