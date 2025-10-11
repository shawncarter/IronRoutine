from django.core.management.base import BaseCommand
from exercises.models import Exercise
from pathlib import Path
from django.conf import settings
import csv


class Command(BaseCommand):
    help = 'Generate a CSV file of missing video URLs for download_from_failures.py script'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='failures.csv',
            help='Output CSV file path (default: failures.csv in project root)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of URLs to generate (for testing)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        limit = options.get('limit')
        
        # Collect all missing video URLs
        rows = []
        
        # Get exercises with male_url or female_url but missing videos
        exercises = Exercise.objects.filter(has_videos=False).exclude(male_url='').exclude(male_url__isnull=True)
        exercises = exercises | Exercise.objects.filter(has_videos=False).exclude(female_url='').exclude(female_url__isnull=True)
        exercises = exercises.distinct().order_by('muscle', 'title', 'name')
        
        for exercise in exercises:
            title = exercise.title or exercise.name
            equipment = exercise.equipment or ''
            muscle = exercise.muscle or ''
            slug = exercise.slug or ''
            
            # Add male URL if exists
            if exercise.male_url:
                # Create entries for both front and side angles
                for angle in ['front', 'side']:
                    rows.append({
                        'title': f"{title} - Male",
                        'page_url': exercise.male_url,
                        'method': 'auto',
                        'angle': angle,
                        'reason': 'missing_video',
                        'equipment': equipment,
                        'slug': slug,
                    })
            
            # Add female URL if exists
            if exercise.female_url:
                # Create entries for both front and side angles
                for angle in ['front', 'side']:
                    rows.append({
                        'title': f"{title} - Female",
                        'page_url': exercise.female_url,
                        'method': 'auto',
                        'angle': angle,
                        'reason': 'missing_video',
                        'equipment': equipment,
                        'slug': slug,
                    })
        
        # Apply limit if specified
        if limit:
            rows = rows[:limit]
        
        # Write CSV file in the format expected by download_from_failures.py
        output_path = Path(settings.BASE_DIR) / output_file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            # CSV format matching failures.csv: title,page_url,method,angle,reason,equipment,slug
            fieldnames = ['title', 'page_url', 'method', 'angle', 'reason', 'equipment', 'slug']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCSV generated: {output_path}\n'
            f'Total rows: {len(rows)}\n'
            f'Ready to use with: python download_from_failures.py --failures-csv {output_file}\n'
        ))
