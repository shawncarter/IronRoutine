from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Exercise, MuscleGroup


def exercise_list(request):
    exercises = Exercise.objects.all().order_by('name')
    muscle_groups = MuscleGroup.objects.all().order_by('name')
    
    # Apply filters
    search = request.GET.get('search', '')
    muscle_group = request.GET.get('muscle_group', '')
    difficulty = request.GET.get('difficulty', '')
    
    if search:
        exercises = exercises.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(muscle_groups__name__icontains=search)
        ).distinct()
    
    if muscle_group:
        exercises = exercises.filter(muscle_groups__name__icontains=muscle_group)
    
    if difficulty:
        exercises = exercises.filter(difficulty=difficulty)
    
    context = {
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'current_search': search,
        'current_muscle_group': muscle_group,
        'current_difficulty': difficulty,
    }
    return render(request, 'exercises/exercise_list.html', context)


def exercise_detail(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    # Get related exercises (same muscle groups)
    related_exercises = Exercise.objects.filter(
        muscle_groups__in=exercise.muscle_groups.all()
    ).exclude(id=exercise.id).distinct()[:4]
    
    context = {
        'exercise': exercise,
        'related_exercises': related_exercises,
    }
    return render(request, 'exercises/exercise_detail.html', context)


def exercise_search(request):
    query = request.GET.get('q', '')
    exercises = []
    
    if query:
        exercises = Exercise.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(muscle_groups__name__icontains=query)
        ).distinct()[:10]
    
    context = {
        'exercises': exercises,
        'query': query,
    }
    return render(request, 'exercises/exercise_search.html', context)
