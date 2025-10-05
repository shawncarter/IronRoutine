from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from routines.models import Routine
from exercises.models import Exercise


class WorkoutSession(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='workout_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='in_progress')
    notes = models.TextField(blank=True)
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total weight lifted
    
    def __str__(self):
        return f"{self.routine.name} - {self.started_at.strftime('%Y-%m-%d')}"
    
    def get_duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at
    
    def calculate_total_volume(self):
        total = sum([ws.volume for ws in self.workout_sets.all()])
        self.total_volume = total
        self.save()
        return total
    
    def get_exercises_completed(self):
        return self.workout_sets.values('exercise').distinct().count()
    
    class Meta:
        ordering = ['-started_at']


class WorkoutSet(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='workout_sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    set_number = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=6, decimal_places=2)  # Weight lifted
    reps = models.PositiveIntegerField()  # Number of repetitions
    volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # weight × reps
    rest_time_actual = models.PositiveIntegerField(null=True, blank=True)  # Actual rest time taken
    completed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Automatically calculate volume when saving
        self.volume = self.weight * self.reps
        super().save(*args, **kwargs)
        # Update session total volume
        self.session.calculate_total_volume()
    
    def __str__(self):
        return f"{self.exercise.name} - Set {self.set_number}: {self.weight}kg × {self.reps} reps"
    
    class Meta:
        ordering = ['completed_at']
        unique_together = ['session', 'exercise', 'set_number']
