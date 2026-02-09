from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    student_id = models.CharField(max_length=20, unique=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.student_id})"

# Create your models here.
