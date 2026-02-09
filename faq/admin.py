from django.contrib import admin
from .models import Category, FAQ, FAQVector, Feedback

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    search_fields = ('name', 'description')
    list_filter = ('parent',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'subtheme', 'is_active')
    search_fields = ('question', 'answer', 'subtheme')
    list_filter = ('category', 'is_active')

@admin.register(FAQVector)
class FAQVectorAdmin(admin.ModelAdmin):
    list_display = ('faq', 'norm', 'computed_at')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('faq', 'feedback_type', 'score', 'resolved', 'created_at')
    list_filter = ('feedback_type', 'resolved', 'resolved')

# Register your models here.
