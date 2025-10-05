from django.contrib import admin
from .models import MuscleGroup, Exercise


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty', 'get_muscle_groups_display', 'equipment_needed']
    list_filter = ['difficulty', 'muscle_groups', 'equipment_needed']
    search_fields = ['name', 'description']
    filter_horizontal = ['muscle_groups']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'muscle_groups', 'difficulty')
        }),
        ('Details', {
            'fields': ('description', 'instructions', 'equipment_needed')
        }),
        ('Media', {
            'fields': ('video_url',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
