from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "start_date", "end_date", "is_featured", "created_at"]
    list_filter = ["status", "is_featured"]
    search_fields = ["title", "description", "location"]
    prepopulated_fields = {"slug": ("title",)}
