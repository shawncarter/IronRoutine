from django.db import models
from django.contrib.auth.models import User
import json


class MuscleGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('Novice', 'Novice'),
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    
    EQUIPMENT_CHOICES = [
        ('barbell', 'Barbell'),
        ('dumbbells', 'Dumbbells'),
        ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine'),
        ('kettlebells', 'Kettlebells'),
        ('stretches', 'Stretches'),
        ('other', 'Other'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    equipment = models.CharField(max_length=50, choices=EQUIPMENT_CHOICES, default='other')
    muscle = models.CharField(max_length=100, blank=True)  # Primary muscle group
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    
    # URLs and videos
    male_url = models.URLField(blank=True, null=True)
    female_url = models.URLField(blank=True, null=True)
    
    # Video paths (stored as JSON)
    male_videos = models.JSONField(default=dict, blank=True)  # {"front": "path", "side": "path"}
    female_videos = models.JSONField(default=dict, blank=True)
    has_videos = models.BooleanField(default=False)
    
    # Instructions (stored as JSON array)
    instructions = models.JSONField(default=list, blank=True)
    
    # Additional fields from JSON
    force = models.CharField(max_length=100, blank=True)
    grips = models.CharField(max_length=100, blank=True)
    mechanic = models.CharField(max_length=100, blank=True)
    
    # Legacy fields for compatibility
    name = models.CharField(max_length=200, blank=True)  # Will be populated from title
    muscle_groups = models.ManyToManyField(MuscleGroup, related_name='exercises', blank=True)
    description = models.TextField(blank=True)
    equipment_needed = models.CharField(max_length=200, blank=True)  # Will be populated from equipment
    video_url = models.URLField(blank=True, null=True)  # Will use male_url as default
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Populate legacy fields for compatibility
        if not self.name:
            self.name = self.title
        if not self.equipment_needed:
            self.equipment_needed = self.get_equipment_display()
        if not self.video_url and self.male_url:
            self.video_url = self.male_url
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title or self.name
    
    def get_muscle_groups_display(self):
        return ", ".join([mg.name for mg in self.muscle_groups.all()])
    
    def get_instructions_list(self):
        """Return instructions as a clean list, handling both JSON and text formats"""
        if isinstance(self.instructions, list):
            return [instruction.replace('\\', '') for instruction in self.instructions]
        elif isinstance(self.instructions, str):
            return [self.instructions]
        return []
    
    def get_video_urls(self, gender='male'):
        """Get video URLs for specified gender"""
        videos = self.male_videos if gender == 'male' else self.female_videos
        return videos if isinstance(videos, dict) else {}
    
    class Meta:
        ordering = ['title', 'name']
