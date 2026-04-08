# Modèles de Données

Documentation des modèles Django et schémas de base de données.

## Organisation

### Par application

- `models-faq.md` - Modèles de l'app FAQ
- `models-users.md` - Modèles de l'app Users
- `models-chatbot.md` - Modèles de l'app ChatBot

### Schémas généraux

- `schema-database.md` - Schéma global de la base
- `migrations-guide.md` - Guide des migrations Django

## Contenu attendu

Pour chaque modèle documenté :

- **Champs** : Type, contraintes, valeur par défaut
- **Relations** : Foreign keys, many-to-many
- **Méthodes** : Fonctions importantes du modèle
- **Usage** : Cas d'utilisation principaux
- **à‰volution** : Changements prévus

## Exemple de structure

```markdown
# Modèle FAQ

## Champs

- `id` : AutoField, clé primaire
- `question` : TextField, nullable=False
- `reponse` : TextField, nullable=False

## Relations

- `categorie` : ForeignKey vers Categorie
- `auteur` : ForeignKey vers User

## Méthodes importantes

- `get_similar_questions()` : Retourne questions similaires
- `validate_content()` : Validation du contenu
```

