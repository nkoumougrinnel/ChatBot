# Rapport — Changement de dépendances et incompatibilité Python 3.13.12

## Contexte

Vous avez mis à jour `requirements.txt` en changeant les versions de `numpy` et `pandas`; les autres paquets ont été résolus automatiquement. Le fichier actif contient désormais :

- asgiref==3.11.1
- Django==4.2.7
- django-cors-headers==4.3.1
- djangorestframework==3.14.0
- joblib==1.5.3
- numpy==2.4.2 (manuellement changé, avant 1.26.2)
- pandas==2.2.3 (manuellement changé, avant 2.1.3)
- python-dateutil==2.9.0.post0
- pytz==2025.2
- scikit-learn==1.5.2 (automatiquement changé, 1.3.2)
- scipy==1.17.0 (automatiquement changé, 1.15.3)
- six==1.17.0
- sqlparse==0.5.5
- threadpoolctl==3.6.0
- tzdata==2025.3

## Observations

- Vous avez tenté de créer l'environnement virtuel et d'installer les dépendances sur Python **3.13.12**.
- L'installation a échoué : cause probable — absence de roues (prebuilt wheels) compatibles pour certaines bibliothèques (notamment celles avec extensions C/C++ comme `scipy` et `scikit-learn`) pour Python 3.13, ce qui force `pip` à compiler depuis les sources et provoque des erreurs si les outils de compilation manquent.
