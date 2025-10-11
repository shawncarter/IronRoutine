#!/bin/bash

# Script to load exercise data from exercise_db.json into the database

echo "=== IronRoutine Exercise Data Loader ==="
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Make migrations for the new model fields
echo ""
echo "Creating migrations for updated Exercise model..."
python manage.py makemigrations exercises

# Apply migrations
echo ""
echo "Applying migrations..."
python manage.py migrate

# Load exercise data from JSON
echo ""
echo "Loading exercise data from exercise_db.json..."
python manage.py load_exercises

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Your exercise database has been populated with data from exercise_db.json"
echo "You can now run the development server with: python manage.py runserver"
