from django.contrib import admin
from .models import Routine, RoutineExercise


class RoutineExerciseInline(admin.TabularInline):
    model = RoutineExercise
    extra = 1
    fields = ['exercise', 'sets_count', 'rest_time_seconds', 'order', 'target_reps', 'target_weight']


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'get_total_exercises', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RoutineExerciseInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
