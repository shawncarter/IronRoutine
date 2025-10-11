# Exercise Database Integration Guide

## Overview

Your IronRoutine app now integrates with the comprehensive `exercise_db.json` database containing:
- **1000+** exercises with detailed instructions
- **Multiple equipment types**: Barbell, Dumbbells, Bodyweight, Machine, Kettlebells, etc.
- **Video demonstrations**: Front and side views for both male and female
- **Difficulty levels**: Novice, Beginner, Intermediate, Advanced
- **Muscle group targeting**: Biceps, Triceps, Chest, Back, Legs, etc.

## What's New

### Enhanced Exercise Model

The `Exercise` model now includes:
- `title` - Exercise name from the database
- `slug` - URL-friendly identifier
- `equipment` - Equipment type (barbell, dumbbells, etc.)
- `muscle` - Primary muscle group
- `difficulty` - Exercise difficulty level
- `male_url` / `female_url` - Links to exercise demonstrations
- `male_videos` / `female_videos` - JSON fields storing video paths
- `instructions` - JSON array of step-by-step instructions
- `has_videos` - Boolean indicating video availability

### New Features

1. **Detailed Exercise Pages**: View exercises with:
   - Step-by-step instructions
   - Video demonstrations (front and side views)
   - Gender-specific demonstrations
   - Related exercises
   - Equipment and difficulty information

2. **Rich Exercise Data**: All exercises from `exercise_db.json` are now available in your app

3. **Video Integration**: Local video files are linked and can be played directly in the browser

## Setup Instructions

### Step 1: Load the Exercise Data

Run the provided setup script:

```bash
./load_exercise_data.sh
```

Or manually run these commands:

```bash
source venv/bin/activate
python manage.py makemigrations exercises
python manage.py migrate
python manage.py load_exercises
```

### Step 2: Verify the Data

Check that exercises were loaded:

```bash
python manage.py shell
>>> from exercises.models import Exercise
>>> Exercise.objects.count()
# Should show 1000+ exercises
>>> Exercise.objects.first().title
# Should show an exercise name
```

### Step 3: Run the Development Server

```bash
python manage.py runserver
```

Visit:
- Exercise list: `http://localhost:8000/exercises/`
- Exercise detail: `http://localhost:8000/exercises/<id>/`
- Create routine: `http://localhost:8000/routines/create/`

## Using the Integration

### Viewing Exercise Details

Navigate to any exercise detail page to see:
- **Instructions**: Numbered step-by-step guide
- **Videos**: Toggle between male/female demonstrations
- **Related Exercises**: Similar exercises based on muscle group and equipment

### Creating Routines

When creating a routine:
1. Browse exercises by muscle group, equipment, or difficulty
2. Click on any exercise to view its details (opens in new tab)
3. Add exercises to your routine with custom sets and rest times

### Video Files

Videos are stored in the `videos/` directory. The paths are stored in the database as:
```json
{
  "male": {
    "front": "videos/Biceps - Dumbbell Curl - Male-front.mp4",
    "side": "videos/Biceps - Dumbbell Curl - Male-side.mp4"
  },
  "female": {
    "front": "videos/Biceps - Dumbbell Curl - Female-front.mp4",
    "side": "videos/Biceps - Dumbbell Curl - Female-side.mp4"
  }
}
```

Make sure your Django static/media files are configured to serve these videos.

## Customization

### Filtering Exercises

The exercise list supports filtering by:
- **Search**: Exercise name or description
- **Muscle Group**: Filter by target muscle
- **Equipment**: Filter by equipment type
- **Difficulty**: Filter by skill level

### Adding Custom Exercises

You can still add custom exercises through the Django admin or by creating them programmatically:

```python
from exercises.models import Exercise

exercise = Exercise.objects.create(
    title="My Custom Exercise",
    slug="my-custom-exercise",
    equipment="dumbbells",
    muscle="biceps",
    difficulty="Beginner",
    instructions=["Step 1", "Step 2", "Step 3"],
    has_videos=False
)
```

## Database Schema

### Exercise Model Fields

| Field | Type | Description |
|-------|------|-------------|
| title | CharField | Exercise name |
| slug | SlugField | URL-friendly identifier |
| equipment | CharField | Equipment type (choices) |
| muscle | CharField | Primary muscle group |
| difficulty | CharField | Difficulty level (choices) |
| male_url | URLField | Male demonstration URL |
| female_url | URLField | Female demonstration URL |
| male_videos | JSONField | Male video paths |
| female_videos | JSONField | Female video paths |
| has_videos | BooleanField | Video availability flag |
| instructions | JSONField | Step-by-step instructions |
| force | CharField | Force type (push/pull) |
| grips | CharField | Grip type |
| mechanic | CharField | Mechanic type |

## Troubleshooting

### Videos Not Playing

1. Check that video files exist in the `videos/` directory
2. Verify Django is configured to serve media files in development:
   ```python
   # settings.py
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'videos'
   ```
3. Add to `urls.py`:
   ```python
   from django.conf import settings
   from django.conf.urls.static import static
   
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

### Exercises Not Loading

1. Verify `exercise_db.json` exists in project root
2. Check file permissions
3. Run with verbose output:
   ```bash
   python manage.py load_exercises --verbosity 2
   ```

### Migration Issues

If you encounter migration conflicts:
```bash
python manage.py migrate exercises zero  # Reset migrations
python manage.py makemigrations exercises
python manage.py migrate
```

## Future Enhancements

Consider adding:
- **Favorites**: Let users favorite exercises
- **Progress Tracking**: Track which exercises users have completed
- **Exercise History**: Show when exercises were last performed
- **Custom Instructions**: Allow users to add personal notes
- **Video Upload**: Enable users to upload their own form check videos

## API Integration (Future)

The exercise data can be exposed via Django REST Framework:

```python
# serializers.py
from rest_framework import serializers
from exercises.models import Exercise

class ExerciseSerializer(serializers.ModelSerializer):
    instructions_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = '__all__'
    
    def get_instructions_list(self, obj):
        return obj.get_instructions_list()
```

## Support

For issues or questions:
1. Check the Django logs
2. Verify database migrations are applied
3. Ensure all dependencies are installed
4. Check that `exercise_db.json` is valid JSON

---

**Happy Training! 💪**
