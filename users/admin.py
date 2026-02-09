from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'student_id', 'department', 'year', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Sup\'ptic', {
            'fields': ('student_id', 'department', 'year', 'phone')
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# Register your models here.
