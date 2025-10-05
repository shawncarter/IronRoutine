# IronRoutine 💪

A Django-based fitness tracking application for managing workout routines, exercises, and tracking workout sessions.

## Features

- **Exercise Management**: Create and manage a database of exercises with muscle groups, difficulty levels, and instructions
- **Routine Builder**: Build custom workout routines by combining exercises with sets, reps, and rest times
- **Workout Tracking**: Start workout sessions and track sets, weights, reps, and total volume
- **Progress History**: View workout history and track progress over time

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
