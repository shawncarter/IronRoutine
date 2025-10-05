from django.contrib import admin
from .models import WorkoutSession, WorkoutSet


class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 0
    readonly_fields = ['volume', 'completed_at']
    fields = ['exercise', 'set_number', 'weight', 'reps', 'volume', 'rest_time_actual', 'completed_at']


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['routine', 'user', 'status', 'total_volume', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at', 'routine__name', 'user']
    search_fields = ['routine__name', 'user__username', 'notes']
    readonly_fields = ['started_at', 'total_volume', 'get_exercises_completed']
    inlines = [WorkoutSetInline]
    
    fieldsets = (
        ('Workout Information', {
            'fields': ('routine', 'user', 'status', 'notes')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Statistics', {
            'fields': ('total_volume', 'get_exercises_completed'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkoutSet)
class WorkoutSetAdmin(admin.ModelAdmin):
    list_display = ['session', 'exercise', 'set_number', 'weight', 'reps', 'volume', 'completed_at']
    list_filter = ['exercise', 'session__routine', 'completed_at']
    search_fields = ['exercise__name', 'session__routine__name', 'notes']
    readonly_fields = ['volume', 'completed_at']
