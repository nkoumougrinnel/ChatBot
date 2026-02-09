from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé conforme à la spécification LaTeX.
    
    Champs hérités d'AbstractUser:
    - id (PRIMARY KEY)
    - email (UNIQUE, NOT NULL)
    - date_joined (TIMESTAMP, auto)
    - last_login (DATETIME, NULL)
    - is_active (BOOLEAN, DEFAULT TRUE)
    
    Champs ajoutés:
    - role (ENUM: etudiant/admin/anonyme, NOT NULL)
    """
    ROLE_CHOICES = [
        ('etudiant', 'Étudiant'),
        ('admin', 'Administrateur'),
        ('anonyme', 'Anonyme'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='anonyme',
        verbose_name="Rôle"
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.role})"
