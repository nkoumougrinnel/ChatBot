# Paramètres Ollama — Phi-3 Mini

## Modèle utilisé
- **Modèle** : `phi3:mini`
- **URL** : `http://localhost:11434`

## Paramètres de génération

| Paramètre | Valeur | Rôle |
|---|---|---|
| `temperature` | `0.3` | Faible pour des réponses factuelles et stables |
| `num_predict` | `150` | Nombre maximum de tokens générés |
| `top_p` | `0.9` | Diversité du texte généré (nucleus sampling) |
| `stop` | `["</s>", "[INST]", "[/INST]"]` | Tokens d'arrêt spécifiques à Phi-3 |

## Pourquoi ces valeurs ?

- **`temperature=0.3`** : On veut des réponses précises et reproductibles, pas créatives. Une valeur basse réduit les hallucinations.
- **`num_predict=150`** : Limite la longueur des réponses pour réduire la latence sur CPU.
- **`top_p=0.9`** : Garde une légère diversité tout en restant cohérent.
- **`stop tokens`** : Empêche Phi-3 de continuer à générer au-delà de la réponse.

## Commandes utiles

```bash
# Démarrer Ollama
ollama serve

# Télécharger le modèle
ollama pull phi3:mini

# Tester manuellement
ollama run phi3:mini "Bonjour, réponds en français"

# Lister les modèles disponibles
ollama list
