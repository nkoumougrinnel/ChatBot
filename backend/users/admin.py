from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
	# Afficher le role et champs principaux dans la liste
	list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
	# Ajouter `role` dans les champs modifiables depuis l'admin
	fieldsets = UserAdmin.fieldsets + (
		('Informations supplémentaires', {'fields': ('role',)}),
	)
