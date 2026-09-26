from django.contrib import admin
from .models import AcademicEvent, EventCategory


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']
    search_fields = ['name']


@admin.register(AcademicEvent)
class AcademicEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'start_date', 'end_date', 'is_all_day']
    list_filter = ['category', 'is_all_day', 'start_date']
    search_fields = ['title', 'description']
    filter_horizontal = ['programs']