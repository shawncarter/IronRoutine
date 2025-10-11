# IronRoutine 💪

A Django-based fitness tracking application for managing workout routines, exercises, and tracking workout sessions.

## Features

- **Comprehensive Exercise Database**: 1000+ exercises with detailed instructions and video demonstrations
- **Exercise Management**: Browse exercises by muscle group, equipment type, and difficulty level
- **Video Demonstrations**: Front and side view videos for both male and female demonstrations
- **Routine Builder**: Build custom workout routines by combining exercises with sets, reps, and rest times
- **Workout Tracking**: Start workout sessions and track sets, weights, reps, and total volume
- **Progress History**: View workout history and track progress over time

## 🎉 New: Exercise Database Integration

IronRoutine now includes a comprehensive exercise database with:
- **1000+ exercises** from `exercise_db.json`
- **Step-by-step instructions** for each exercise
- **Video demonstrations** (front and side views)
- **Multiple equipment types**: Barbell, Dumbbells, Bodyweight, Machine, Kettlebells, Cables, Bands
- **Difficulty levels**: Novice, Beginner, Intermediate, Advanced
- **Muscle group targeting**: All major muscle groups covered

### Quick Start - Load Exercise Data

```bash
# Run the setup script to load all exercises
./load_exercise_data.sh
```

Or manually:
```bash
source venv/bin/activate
python manage.py makemigrations exercises
python manage.py migrate
python manage.py load_exercises
```

See [EXERCISE_INTEGRATION.md](EXERCISE_INTEGRATION.md) for detailed documentation.

## Project Structure

- **exercises/**: Exercise database management (exercises, muscle groups)
- **routines/**: Workout routine creation and management
- **workouts/**: Active workout sessions and workout history
- **templates/**: HTML templates with responsive design
- **static/**: CSS, JavaScript, and image assets

## Models

### Exercise App
- `MuscleGroup`: Categorize exercises by muscle groups
- `Exercise`: Exercise database with instructions, difficulty, equipment needed

### Routines App
- `Routine`: User workout routines
- `RoutineExercise`: Exercises within routines with sets/reps configuration

### Workouts App
- `WorkoutSession`: Active or completed workout sessions
- `WorkoutSet`: Individual sets performed during workouts

## Technology Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite3 (development)
- **Frontend**: HTML templates with custom CSS
- **Authentication**: Django's built-in auth system (currently using default user)

## Getting Started

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install django
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Current Status

This is a work-in-progress fitness tracking application. Current features include:
- Basic exercise database
- Routine creation and management
- Workout session tracking
- Simple user interface

## Future Enhancements

- User authentication and profiles
- Exercise images and videos
- Progress charts and analytics
- Mobile-responsive design improvements
- REST API for mobile app integration
- Social features and workout sharing

## License

This project is open source and available under the MIT License.
