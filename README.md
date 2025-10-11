# IronRoutine 💪

A modern Django-based fitness tracking application for managing workout routines, browsing exercises, and tracking workout sessions with a professional Bootstrap 5 interface.

## ✨ Features

### 🏋️ Exercise Library
- **1000+ exercises** from comprehensive exercise database
- **Advanced filtering** by muscle group, equipment type, difficulty level, and search
- **Server-side filtering** for fast, responsive performance
- **Clickable badges** for quick filtering by category
- **Video demonstrations** with front and side views for male and female
- **Detailed instructions** for proper form and execution
- **Bootstrap 5 cards** with professional, consistent styling

### 📋 Routine Builder
- **Drag-and-drop routine creation** with exercise selection
- **Real-time filtering** while building routines
- **LocalStorage persistence** - your routine draft is saved automatically
- **Customizable sets and rest times** for each exercise
- **Video preview modal** to check exercise form before adding
- **Responsive design** that works on desktop and mobile

### 📊 Workout Tracking
- **Start workout sessions** from your saved routines
- **Track sets, weights, and reps** in real-time
- **Calculate total volume** automatically
- **Workout history** with detailed session logs
- **Progress tracking** over time

### 🎨 Modern UI/UX
- **Bootstrap 5** for professional, responsive design
- **Consistent filtering** across Exercise Library and Routine Create pages
- **Intuitive card layout** with badges at top, description in middle, actions at bottom
- **Color-coded difficulty badges** (Green → Yellow → Orange → Red)
- **Outline buttons** for distinctive, accessible actions
- **Smooth hover effects** and transitions

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

## 🛠️ Technology Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite3 (included in repository)
- **Frontend**: Bootstrap 5.3.0, HTML5, JavaScript (ES6+)
- **Icons**: Bootstrap Icons 1.11.0
- **Styling**: Custom CSS with Bootstrap utilities
- **Storage**: LocalStorage for routine draft persistence
- **Video Hosting**: Static file serving for MP4 videos

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

## 📈 Current Status

IronRoutine is a fully functional fitness tracking application with:
- ✅ Complete exercise database (1000+ exercises)
- ✅ Advanced filtering and search
- ✅ Routine creation with localStorage persistence
- ✅ Video demonstrations for exercises
- ✅ Bootstrap 5 modern UI
- ✅ Workout session tracking
- ✅ Responsive design

## 🚀 Future Enhancements

- [ ] **User authentication** - Multi-user support with personal routines
- [ ] **Progress charts** - Visual analytics and progress tracking
- [ ] **Exercise images** - Thumbnail images for quick reference
- [ ] **REST API** - Mobile app integration
- [ ] **Social features** - Share routines and workouts
- [ ] **Workout templates** - Pre-built routines for common goals
- [ ] **Exercise notes** - Personal notes and modifications
- [ ] **Export/Import** - Backup and share routines as JSON
- [ ] **Progressive overload tracking** - Automatic weight progression suggestions
- [ ] **Workout timer** - Built-in rest timer and workout duration tracking

## License

This project is open source and available under the MIT License.
