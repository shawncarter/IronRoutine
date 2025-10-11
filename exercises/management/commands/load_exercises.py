import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from exercises.models import Exercise, MuscleGroup


class Command(BaseCommand):
    help = 'Load exercises from exercise_db.json into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='exercise_db.json',
            help='Path to the exercise JSON file (default: exercise_db.json in project root)'
        )

    def handle(self, *args, **options):
        json_file = options['file']
        
        # If relative path, assume it's in project root
        if not os.path.isabs(json_file):
            json_file = os.path.join(settings.BASE_DIR, json_file)
        
        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Loading exercises from: {json_file}'))
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            exercises_data = data.get('exercises', [])
            
            if not exercises_data:
                self.stdout.write(self.style.WARNING('No exercises found in JSON file'))
                return
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for exercise_data in exercises_data:
                try:
                    # Extract data from JSON
                    title = exercise_data.get('title', '')
                    slug = exercise_data.get('slug', '')
                    
                    if not title or not slug:
                        self.stdout.write(self.style.WARNING(f'Skipping exercise with missing title or slug'))
                        skipped_count += 1
                        continue
                    
                    # Map equipment to our choices
                    equipment = exercise_data.get('equipment', 'other')
                    if equipment == 'cables':
                        equipment = 'other'
                    elif equipment == 'band':
                        equipment = 'other'
                    
                    # Get or create muscle group
                    muscle_name = exercise_data.get('muscle', 'general')
                    muscle_group, _ = MuscleGroup.objects.get_or_create(
                        name=muscle_name.title()
                    )
                    
                    # Prepare exercise data
                    exercise_defaults = {
                        'title': title,
                        'equipment': equipment,
                        'muscle': muscle_name,
                        'difficulty': exercise_data.get('difficulty', 'Beginner'),
                        'male_url': exercise_data.get('urls', {}).get('male', ''),
                        'female_url': exercise_data.get('urls', {}).get('female', ''),
                        'male_videos': exercise_data.get('videos', {}).get('male', {}),
                        'female_videos': exercise_data.get('videos', {}).get('female', {}),
                        'has_videos': exercise_data.get('has_videos', False),
                        'instructions': exercise_data.get('instructions', []),
                        'force': exercise_data.get('force', ''),
                        'grips': exercise_data.get('grips', ''),
                        'mechanic': exercise_data.get('mechanic', ''),
                    }
                    
                    # Create or update exercise
                    exercise, created = Exercise.objects.update_or_create(
                        slug=slug,
                        defaults=exercise_defaults
                    )
                    
                    # Add muscle group relationship
                    exercise.muscle_groups.add(muscle_group)
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'Created: {title}')
                    else:
                        updated_count += 1
                        self.stdout.write(f'Updated: {title}')
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing exercise: {str(e)}'))
                    skipped_count += 1
                    continue
            
            self.stdout.write(self.style.SUCCESS(
                f'\nCompleted! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'
            ))
            
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
