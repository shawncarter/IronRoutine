from django.core.management.base import BaseCommand
from exercises.models import Exercise
from pathlib import Path
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Scan videos directory and update exercise video status in database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--videos-dir',
            type=str,
            default='videos',
            help='Directory containing video files (default: videos)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        videos_dir = options['videos_dir']
        dry_run = options['dry_run']
        
        # Get absolute path to videos directory
        if not os.path.isabs(videos_dir):
            videos_dir = os.path.join(settings.BASE_DIR, videos_dir)
        
        if not os.path.exists(videos_dir):
            self.stdout.write(self.style.ERROR(f'Videos directory not found: {videos_dir}'))
            return
        
        self.stdout.write(f'Scanning videos directory: {videos_dir}')
        
        # Get all video files
        video_files = {}
        for filename in os.listdir(videos_dir):
            if filename.endswith('.mp4'):
                video_files[filename] = os.path.join(videos_dir, filename)
        
        self.stdout.write(f'Found {len(video_files)} video files')
        
        # Get exercises that currently have has_videos=False
        exercises_without_videos = Exercise.objects.filter(has_videos=False)
        total_exercises = exercises_without_videos.count()
        
        self.stdout.write(f'Checking {total_exercises} exercises without videos...\n')
        
        updated_count = 0
        
        for exercise in exercises_without_videos:
            title = exercise.title or exercise.name
            muscle = exercise.muscle or ''
            
            # Build expected filenames based on the download script's naming convention:
            # Muscle - Exercise - Gender-angle.mp4
            muscle_display = muscle.replace('-', ' ').title() if muscle else ''
            
            expected_files = []
            if muscle_display:
                expected_files = [
                    f"{muscle_display} - {title} - Male-front.mp4",
                    f"{muscle_display} - {title} - Male-side.mp4",
                    f"{muscle_display} - {title} - Female-front.mp4",
                    f"{muscle_display} - {title} - Female-side.mp4",
                ]
            
            # Check if any of the expected files exist
            found_videos = []
            for expected_file in expected_files:
                if expected_file in video_files:
                    found_videos.append(expected_file)
            
            # If we found at least some videos, update the exercise
            if found_videos:
                # Build the video paths dictionary
                male_videos = {}
                female_videos = {}
                
                for video_file in found_videos:
                    video_path = f"videos/{video_file}"
                    
                    if 'Male-front' in video_file:
                        male_videos['front'] = video_path
                    elif 'Male-side' in video_file:
                        male_videos['side'] = video_path
                    elif 'Female-front' in video_file:
                        female_videos['front'] = video_path
                    elif 'Female-side' in video_file:
                        female_videos['side'] = video_path
                
                # Update the exercise
                if not dry_run:
                    if male_videos:
                        exercise.male_videos = male_videos
                    if female_videos:
                        exercise.female_videos = female_videos
                    
                    # Set has_videos to True if we have at least one complete set
                    if (male_videos.get('front') and male_videos.get('side')) or \
                       (female_videos.get('front') and female_videos.get('side')):
                        exercise.has_videos = True
                    
                    exercise.save()
                
                updated_count += 1
                status = '[DRY RUN] Would update' if dry_run else '✓ Updated'
                self.stdout.write(
                    f'{status}: {title} - Found {len(found_videos)} videos'
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN: Would update {updated_count} exercises'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Updated {updated_count} exercises with video data'
            ))
        
        remaining = total_exercises - updated_count
        self.stdout.write(f'Remaining exercises without videos: {remaining}')
