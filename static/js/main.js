// Global timer variables
let restTimer = null;
let restTimeRemaining = 0;

// Timer functions
function startRestTimer(seconds) {
    if (restTimer) {
        clearInterval(restTimer);
    }
    
    restTimeRemaining = seconds;
    updateTimerDisplay();
    
    const timerElement = document.getElementById('rest-timer');
    if (timerElement) {
        timerElement.classList.remove('hidden');
        timerElement.style.display = 'flex';
        timerElement.setAttribute('data-active-timer', 'true');
    }
    
    restTimer = setInterval(() => {
        restTimeRemaining--;
        updateTimerDisplay();
        
        if (restTimeRemaining <= 0) {
            clearInterval(restTimer);
            onTimerComplete();
        }
    }, 1000);
}

function stopRestTimer() {
    if (restTimer) {
        clearInterval(restTimer);
        restTimer = null;
    }
    
    const timerElement = document.getElementById('rest-timer');
    if (timerElement) {
        timerElement.classList.add('hidden');
        timerElement.style.display = 'none';
        timerElement.removeAttribute('data-active-timer');
    }
}

function updateTimerDisplay() {
    const minutes = Math.floor(restTimeRemaining / 60);
    const seconds = restTimeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    const displayElement = document.getElementById('timer-display');
    if (displayElement) {
        displayElement.textContent = display;
    }
}

function onTimerComplete() {
    const timerElement = document.getElementById('rest-timer');
    if (timerElement) {
        timerElement.innerHTML = `
            <div class="timer-display">
                <div>Rest Complete! 🎯</div>
                <div style="font-size: 1rem; margin-top: 0.5rem;">Ready for next set</div>
            </div>
            <div class="timer-controls">
                <button class="btn btn-primary" onclick="hideTimer()">Continue</button>
            </div>
        `;
    }
    
    // Play notification sound (if supported)
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBT6azvO+ZykNJoPQ8diKOgsnfM7y2IlDA');
        audio.play();
    } catch (e) {
        // Silent fail if audio not supported
    }
}

function hideTimer() {
    const timerElement = document.getElementById('rest-timer');
    if (timerElement) {
        timerElement.classList.add('hidden');
        timerElement.style.display = 'none';
        timerElement.removeAttribute('data-active-timer');
    }
}

// Form handling functions
function saveWorkoutSet(sessionId, exerciseId, setNumber) {
    const weightInput = document.querySelector(`input[name="weight_${setNumber}"]`);
    const repsInput = document.querySelector(`input[name="reps_${setNumber}"]`);
    
    if (!weightInput || !repsInput) {
        alert('Please fill in both weight and reps');
        return;
    }
    
    const weight = parseFloat(weightInput.value);
    const reps = parseInt(repsInput.value);
    
    if (isNaN(weight) || isNaN(reps) || weight <= 0 || reps <= 0) {
        alert('Please enter valid weight and reps');
        return;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('exercise_id', exerciseId);
    formData.append('set_number', setNumber);
    formData.append('weight', weight);
    formData.append('reps', reps);
    formData.append('csrfmiddlewaretoken', getCsrfToken());
    
    // Send to server
    fetch('/workouts/set/save/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to show set as completed
            const setRow = document.querySelector(`#set-${setNumber}`);
            if (setRow) {
                setRow.classList.add('completed');
                setRow.innerHTML += '<span class="set-complete-badge">✓</span>';
            }
            
            // Update volume display
            const volume = weight * reps;
            const volumeElement = document.querySelector(`#volume-${setNumber}`);
            if (volumeElement) {
                volumeElement.textContent = `${volume.toFixed(1)}kg`;
            }
            
            // Start rest timer if specified
            if (data.rest_time && data.rest_time > 0) {
                startRestTimer(data.rest_time);
            }
            
            // Disable inputs
            weightInput.disabled = true;
            repsInput.disabled = true;
            
            // Update save button
            const saveButton = document.querySelector(`#save-btn-${setNumber}`);
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.textContent = 'Saved';
                saveButton.classList.remove('btn-primary');
                saveButton.classList.add('btn-secondary');
            }
        } else {
            alert('Error saving set: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving set');
    });
}

// Exercise search and filtering
function filterExercises() {
    const searchTerm = document.getElementById('exercise-search').value.toLowerCase();
    const muscleGroupFilter = document.getElementById('muscle-group-filter').value;
    const difficultyFilter = document.getElementById('difficulty-filter').value;
    
    const exercises = document.querySelectorAll('.exercise-card');
    
    exercises.forEach(card => {
        const title = card.querySelector('.card-title').textContent.toLowerCase();
        const muscleGroups = Array.from(card.querySelectorAll('.muscle-group-tag'))
            .map(tag => tag.textContent.toLowerCase());
        const difficulty = card.querySelector('.difficulty-badge').textContent.toLowerCase();
        
        let show = true;
        
        // Search term filter
        if (searchTerm && !title.includes(searchTerm)) {
            show = false;
        }
        
        // Muscle group filter
        if (muscleGroupFilter && !muscleGroups.some(mg => mg.includes(muscleGroupFilter.toLowerCase()))) {
            show = false;
        }
        
        // Difficulty filter
        if (difficultyFilter && !difficulty.includes(difficultyFilter.toLowerCase())) {
            show = false;
        }
        
        card.style.display = show ? 'block' : 'none';
    });
}

// Routine builder functions
function addExerciseToRoutine(exerciseId, exerciseName) {
    const routineExercises = document.getElementById('routine-exercises');
    if (!routineExercises) return;
    
    // Check if exercise already added - look only within the routine exercises container
    if (routineExercises.querySelector(`.routine-exercise-item[data-exercise-id="${exerciseId}"]`)) {
        alert('Exercise already added to routine');
        return;
    }
    
    // Remove empty state message if it exists
    const emptyState = routineExercises.querySelector('.text-center.text-muted');
    if (emptyState) {
        emptyState.remove();
    }
    
    const exerciseDiv = document.createElement('div');
    exerciseDiv.className = 'routine-exercise-item';
    exerciseDiv.setAttribute('data-exercise-id', exerciseId);
    
    exerciseDiv.innerHTML = `
        <div class="flex justify-between items-center">
            <div class="exercise-info">
                <h4>${exerciseName}</h4>
                <input type="hidden" name="exercise_${exerciseId}" value="1">
            </div>
            <div class="exercise-controls flex gap-2 items-center">
                <label>Sets:</label>
                <input type="number" name="sets_${exerciseId}" value="3" min="1" max="10" class="form-control" style="width: 80px;">
                <label>Rest (sec):</label>
                <input type="number" name="rest_${exerciseId}" value="60" min="30" max="300" step="15" class="form-control" style="width: 100px;">
                <button type="button" class="btn btn-danger btn-sm" onclick="removeExerciseFromRoutine(${exerciseId})">Remove</button>
            </div>
        </div>
    `;
    
    routineExercises.appendChild(exerciseDiv);
    updateExerciseCount();
}

function removeExerciseFromRoutine(exerciseId) {
    const exerciseElement = document.querySelector(`[data-exercise-id="${exerciseId}"]`);
    if (exerciseElement) {
        exerciseElement.remove();
        updateExerciseCount();
    }
}

function updateExerciseCount() {
    const count = document.querySelectorAll('.routine-exercise-item').length;
    const countElement = document.getElementById('exercise-count');
    if (countElement) {
        countElement.textContent = count;
    }
}

// Utility functions
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up search functionality
    const searchInput = document.getElementById('exercise-search');
    if (searchInput) {
        searchInput.addEventListener('input', filterExercises);
    }
    
    const muscleGroupFilter = document.getElementById('muscle-group-filter');
    if (muscleGroupFilter) {
        muscleGroupFilter.addEventListener('change', filterExercises);
    }
    
    const difficultyFilter = document.getElementById('difficulty-filter');
    if (difficultyFilter) {
        difficultyFilter.addEventListener('change', filterExercises);
    }
    
    // Only resume timers if they were actually active (not just the default HTML)
    const timerElement = document.getElementById('rest-timer');
    if (timerElement && !timerElement.classList.contains('hidden')) {
        // Only resume if there's a specific marker indicating an active timer
        if (timerElement.hasAttribute('data-active-timer')) {
            const timeValue = document.getElementById('timer-display');
            if (timeValue) {
                const timeStr = timeValue.textContent;
                const [minutes, seconds] = timeStr.split(':').map(Number);
                if (!isNaN(minutes) && !isNaN(seconds)) {
                    startRestTimer(minutes * 60 + seconds);
                }
            }
        }
    }
});

// Workout completion
function completeWorkout(sessionId) {
    if (confirm('Complete this workout? This cannot be undone.')) {
        window.location.href = `/workouts/session/${sessionId}/complete/`;
    }
}