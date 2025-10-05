from django.db import models
from django.contrib.auth.models import User
from exercises.models import Exercise


class Routine(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def get_total_exercises(self):
        return self.routine_exercises.count()
    
    def get_estimated_duration(self):
        # Rough estimate: 2-3 minutes per set + rest time
        total_sets = sum([re.sets_count for re in self.routine_exercises.all()])
        estimated_minutes = total_sets * 3  # 3 minutes per set average
        return estimated_minutes
    
    class Meta:
        ordering = ['-created_at']


class RoutineExercise(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='routine_exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets_count = models.PositiveIntegerField(default=3)
    rest_time_seconds = models.PositiveIntegerField(default=60)  # Rest time between sets
    order = models.PositiveIntegerField(default=0)  # Order of exercise in routine
    target_reps = models.CharField(max_length=50, blank=True)  # e.g., "8-12", "to failure"
    target_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.routine.name} - {self.exercise.name} ({self.sets_count} sets)"
    
    class Meta:
        ordering = ['order']
        unique_together = ['routine', 'exercise']
