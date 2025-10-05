from django.db import models
from django.contrib.auth.models import User


class MuscleGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    name = models.CharField(max_length=200)
    muscle_groups = models.ManyToManyField(MuscleGroup, related_name='exercises')
    description = models.TextField()
    instructions = models.TextField()
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY_CHOICES, default='beginner')
    equipment_needed = models.CharField(max_length=200, blank=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_muscle_groups_display(self):
        return ", ".join([mg.name for mg in self.muscle_groups.all()])
    
    class Meta:
        ordering = ['name']
