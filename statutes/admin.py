from django.contrib import admin
from .models import StatuteCategory, Statute


@admin.register(StatuteCategory)
class StatuteCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_sw', 'sort_order', 'is_active', 'deleted_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_sw')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Statute)
class StatuteAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_sw', 'is_active', 'file_size', 'deleted_at', 'created_at')
    list_filter = ('is_active', 'categories')
    search_fields = ('title', 'title_sw')
    filter_horizontal = ('categories',)
