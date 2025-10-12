# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IronRoutine is a Django-based fitness tracking application that manages workout routines, exercise databases, and workout sessions. The app includes a comprehensive exercise database with 1000+ exercises from `exercise_db.json`, complete with video demonstrations and detailed instructions.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (Django is the main requirement)
pip install django

# Additional dependencies for scraping tools (optional)
pip install -r requirements.txt
```

### Database Operations
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Load exercise data from JSON (essential for full functionality)
./load_exercise_data.sh
# Or manually:
python manage.py makemigrations exercises
python manage.py migrate
python manage.py load_exercises

# Create superuser for admin access
python manage.py createsuperuser
```

### Running the Application
```bash
# Start development server
python manage.py runserver

# Access Django admin
# http://localhost:8000/admin/

# Main application URLs
# http://localhost:8000/exercises/ - Exercise library
# http://localhost:8000/routines/ - Routine management
# http://localhost:8000/workouts/ - Workout tracking
```

### Data Management
```bash
# Query exercises in Python shell
python manage.py shell
>>> from exercises.models import Exercise
>>> Exercise.objects.count()  # Should show 1000+ after data load

# Check for missing data
python check_missing.py

# Query exercise database directly
python query_exercises.py
```

## Architecture

### Django Apps Structure
- **exercises/**: Exercise database management
  - Models: `Exercise`, `MuscleGroup`
  - Contains exercise data with videos, instructions, muscle groups, equipment types
  - Management command: `load_exercises` for importing from JSON

- **routines/**: Workout routine creation and management
  - Models: `Routine`, `RoutineExercise`
  - Drag-and-drop routine builder with localStorage persistence

- **workouts/**: Active workout sessions and history
  - Models: `WorkoutSession`, `WorkoutSet`
  - Real-time workout tracking with sets, weights, and reps

### Key Models

**Exercise Model** (`exercises/models.py:14-96`):
- Stores exercise data from `exercise_db.json`
- Fields: title, slug, equipment, muscle, difficulty, instructions (JSON), videos (JSON)
- Legacy compatibility fields for existing functionality
- Equipment choices: barbell, dumbbells, bodyweight, machine, kettlebells, stretches, other
- Difficulty levels: Novice, Beginner, Intermediate, Advanced

**Video Integration**:
- Videos stored as JSON fields with male/female and front/side views
- Video files expected in `videos/` directory
- Static file serving configured in settings for video access

### Database
- Uses SQLite3 (`db.sqlite3`) included in repository
- Exercise data populated from `exercise_db.json` (1000+ exercises)
- Database is pre-populated and committed to repository

### Frontend
- Bootstrap 5.3.0 for responsive UI
- Custom JavaScript for filtering and drag-and-drop functionality
- LocalStorage for routine draft persistence
- Video players for exercise demonstrations

## Exercise Data System

The application uses a comprehensive exercise database loaded from `exercise_db.json`:

### Loading Exercise Data
The `load_exercises` management command (`exercises/management/commands/load_exercises.py`) imports exercise data:
- Reads from `exercise_db.json` in project root
- Creates/updates Exercise and MuscleGroup models
- Maps equipment types to Django choices
- Handles video URLs and instruction data

### Exercise Database Tools
Several Python scripts assist with exercise data management:
- `scraper.py`: Web scraping for exercise data
- `build_exercise_db.py`: Builds the exercise database JSON
- `extract_instructions.py`: Extracts step-by-step instructions
- `retry_failures.py` / `download_from_failures.py`: Handle failed data downloads

## Important Files

- `exercise_db.json`: Master exercise database (1000+ exercises)
- `load_exercise_data.sh`: One-command setup script for exercise data
- `EXERCISE_INTEGRATION.md`: Detailed guide for exercise database integration
- `requirements.txt`: Dependencies for data scraping tools (not Django core)

## Development Notes

### Testing
No specific test framework configured. Use Django's built-in testing:
```bash
python manage.py test
```

### Static Files
- Static files configured to serve from `static/` and `videos/` directories
- Video files should be placed in `videos/` directory for exercise demonstrations

### Data Integrity
- Exercise data is loaded from JSON and should not be manually edited in Django admin
- Use the management command to reload data after JSON updates
- Database includes both new JSON-based fields and legacy fields for compatibility