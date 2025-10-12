// Advanced AJAX-based exercise filtering system
class ExerciseFilter {
    constructor(options = {}) {
        this.apiUrl = options.apiUrl || '/exercises/api/exercises/';
        this.containerSelector = options.containerSelector || '.exercise-list';
        this.countSelector = options.countSelector || '.results-count';
        this.loadingSelector = options.loadingSelector || '.loading-indicator';
        this.searchInputSelector = options.searchInputSelector || '#search';
        this.muscleGroupSelector = options.muscleGroupSelector || '#muscle_group';
        this.equipmentSelector = options.equipmentSelector || '#equipment';
        this.difficultySelector = options.difficultySelector || '#difficulty';
        this.pageType = options.pageType || 'list'; // 'list' or 'routine_create'

        this.currentFilters = {
            search: '',
            muscle_group: '',
            equipment: '',
            difficulty: ''
        };

        this.debounceTimer = null;
        this.isLoading = false;

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialFilters();
    }

    bindEvents() {
        console.log('AJAX Filters: Binding events...');

        // Search input with debouncing
        const searchInput = document.querySelector(this.searchInputSelector);
        if (searchInput) {
            console.log('AJAX Filters: Found search input');
            searchInput.addEventListener('input', (e) => {
                console.log('AJAX Filters: Search input changed:', e.target.value);
                this.debounceFilter('search', e.target.value);
            });
        } else {
            console.warn('AJAX Filters: Search input not found:', this.searchInputSelector);
        }

        // Dropdown filters
        const muscleSelect = document.querySelector(this.muscleGroupSelector);
        if (muscleSelect) {
            console.log('AJAX Filters: Found muscle group select');
            muscleSelect.addEventListener('change', (e) => {
                console.log('AJAX Filters: Muscle group changed:', e.target.value);
                this.applyFilter('muscle_group', e.target.value);
            });
        } else {
            console.warn('AJAX Filters: Muscle group select not found:', this.muscleGroupSelector);
        }

        const equipmentSelect = document.querySelector(this.equipmentSelector);
        if (equipmentSelect) {
            console.log('AJAX Filters: Found equipment select');
            equipmentSelect.addEventListener('change', (e) => {
                console.log('AJAX Filters: Equipment changed:', e.target.value);
                this.applyFilter('equipment', e.target.value);
            });
        } else {
            console.warn('AJAX Filters: Equipment select not found:', this.equipmentSelector);
        }

        const difficultySelect = document.querySelector(this.difficultySelector);
        if (difficultySelect) {
            console.log('AJAX Filters: Found difficulty select');
            difficultySelect.addEventListener('change', (e) => {
                console.log('AJAX Filters: Difficulty changed:', e.target.value);
                this.applyFilter('difficulty', e.target.value);
            });
        } else {
            console.warn('AJAX Filters: Difficulty select not found:', this.difficultySelector);
        }

        // Badge filtering
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('clickable-badge')) {
                e.preventDefault();
                e.stopPropagation();

                const filterType = e.target.dataset.filterType;
                const filterValue = e.target.dataset.filterValue;

                if (filterType === 'difficulty') {
                    this.applyFilter('difficulty', filterValue);
                } else if (filterType === 'muscle') {
                    this.applyFilter('muscle_group', filterValue);
                } else if (filterType === 'equipment') {
                    this.applyFilter('equipment', filterValue);
                }
            }
        });
    }

    loadInitialFilters() {
        // Load current filter values from form elements
        const searchInput = document.querySelector(this.searchInputSelector);
        const muscleSelect = document.querySelector(this.muscleGroupSelector);
        const equipmentSelect = document.querySelector(this.equipmentSelector);
        const difficultySelect = document.querySelector(this.difficultySelector);

        if (searchInput) this.currentFilters.search = searchInput.value;
        if (muscleSelect) this.currentFilters.muscle_group = muscleSelect.value;
        if (equipmentSelect) this.currentFilters.equipment = equipmentSelect.value;
        if (difficultySelect) this.currentFilters.difficulty = difficultySelect.value;
    }

    debounceFilter(filterType, value) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.applyFilter(filterType, value);
        }, 300);
    }

    applyFilter(filterType, value) {
        this.currentFilters[filterType] = value;
        this.updateFormElements();
        this.updateUrl();
        this.fetchExercises();
    }

    updateFormElements() {
        // Update form elements to reflect current filters
        const searchInput = document.querySelector(this.searchInputSelector);
        const muscleSelect = document.querySelector(this.muscleGroupSelector);
        const equipmentSelect = document.querySelector(this.equipmentSelector);
        const difficultySelect = document.querySelector(this.difficultySelector);

        if (searchInput && searchInput.value !== this.currentFilters.search) {
            searchInput.value = this.currentFilters.search;
        }
        if (muscleSelect && muscleSelect.value !== this.currentFilters.muscle_group) {
            muscleSelect.value = this.currentFilters.muscle_group;
        }
        if (equipmentSelect && equipmentSelect.value !== this.currentFilters.equipment) {
            equipmentSelect.value = this.currentFilters.equipment;
        }
        if (difficultySelect && difficultySelect.value !== this.currentFilters.difficulty) {
            difficultySelect.value = this.currentFilters.difficulty;
        }
    }

    updateUrl() {
        // Update URL without page refresh
        const url = new URL(window.location);

        Object.keys(this.currentFilters).forEach(key => {
            if (this.currentFilters[key]) {
                url.searchParams.set(key, this.currentFilters[key]);
            } else {
                url.searchParams.delete(key);
            }
        });

        history.pushState({}, '', url);
    }

    async fetchExercises() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading(true);

        try {
            const url = new URL(this.apiUrl, window.location.origin);

            // Add filter parameters
            Object.keys(this.currentFilters).forEach(key => {
                if (this.currentFilters[key]) {
                    url.searchParams.set(key, this.currentFilters[key]);
                }
            });

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.renderExercises(data.exercises, data.count);

            // For routine create page, restore selected exercises
            if (this.pageType === 'routine_create' && typeof loadRoutineFromLocalStorage === 'function') {
                // Small delay to ensure DOM is updated
                setTimeout(() => {
                    loadRoutineFromLocalStorage();
                }, 100);
            }

        } catch (error) {
            console.error('Error fetching exercises:', error);
            this.showError('Failed to load exercises. Please try again.');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    renderExercises(exercises, count) {
        const container = document.querySelector(this.containerSelector);
        if (!container) return;

        // Update count
        this.updateCount(count);

        if (exercises.length === 0) {
            this.renderEmptyState();
            return;
        }

        // Render exercises
        container.innerHTML = exercises.map(exercise => this.renderExerciseCard(exercise)).join('');

        // Re-bind video modal events for routine create page
        if (this.pageType === 'routine_create') {
            this.bindVideoEvents();
        }
    }

    renderExerciseCard(exercise) {
        const title = exercise.title || exercise.name;

        // Generate compact badges
        const difficultyBadge = `<span class="badge bg-${exercise.difficulty.toLowerCase()}-level badge-sm clickable-badge"
                                      data-filter-type="difficulty"
                                      data-filter-value="${exercise.difficulty}"
                                      title="Click to filter by ${exercise.difficulty}"
                                      role="button">
                                    ${exercise.difficulty}
                                  </span>`;

        const muscleBadge = exercise.muscle ? `<span class="badge bg-primary badge-sm clickable-badge"
                                                     data-filter-type="muscle"
                                                     data-filter-value="${exercise.muscle}"
                                                     title="Click to filter by ${exercise.muscle}"
                                                     role="button">
                                                ${exercise.muscle.charAt(0).toUpperCase() + exercise.muscle.slice(1)}
                                              </span>` : '';

        const equipmentBadge = exercise.equipment ? `<span class="badge bg-secondary badge-sm clickable-badge"
                                                           data-filter-type="equipment"
                                                           data-filter-value="${exercise.equipment}"
                                                           title="Click to filter by ${exercise.equipment_display}"
                                                           role="button">
                                                      ${exercise.equipment_display}
                                                    </span>` : '';

        // Different action buttons based on page type
        let actionButtons = '';
        if (this.pageType === 'routine_create') {
            actionButtons = `
                <div class="d-flex gap-1">
                    ${exercise.has_videos ? `
                    <button type="button" class="btn btn-outline-info btn-xs view-video-btn"
                            data-exercise-id="${exercise.id}"
                            data-exercise-title="${title}"
                            data-male-front="${exercise.male_videos?.front || ''}"
                            data-male-side="${exercise.male_videos?.side || ''}"
                            data-female-front="${exercise.female_videos?.front || ''}"
                            data-female-side="${exercise.female_videos?.side || ''}"
                            title="Preview exercise videos">
                        <i class="bi bi-play-circle"></i> Preview
                    </button>` : ''}
                    <button type="button" class="btn btn-outline-success btn-xs add-exercise-btn"
                            data-exercise-id="${exercise.id}"
                            data-exercise-name="${title}">
                        <i class="bi bi-plus-circle"></i> Add
                    </button>
                </div>
            `;
        } else {
            actionButtons = `
                <div class="d-flex gap-2">
                    <a href="/exercises/${exercise.id}/"
                       class="btn btn-outline-primary btn-sm flex-fill">
                        <i class="bi bi-eye"></i> View Details
                    </a>
                </div>
            `;
        }

        // Use compact format for routine create, regular for exercise list
        const cardSpacing = this.pageType === 'routine_create' ? 'mb-2' : 'mb-3';
        const cardBodyPadding = this.pageType === 'routine_create' ? 'py-2 px-3' : '';
        const titleSize = this.pageType === 'routine_create' ? 'h6' : 'h5';
        const description = this.pageType === 'routine_create' ? '' : `<p class="card-text text-muted small mb-3">${exercise.description ? this.truncateText(exercise.description, 15) : ''}</p>`;

        return `
            <div class="card ${cardSpacing} exercise-card"
                 data-exercise-id="${exercise.id}"
                 data-exercise-name="${title}"
                 data-equipment="${exercise.equipment || ''}"
                 data-difficulty="${exercise.difficulty}"
                 data-muscle="${exercise.muscle || ''}">
                <div class="card-body ${cardBodyPadding}">
                    ${this.pageType === 'routine_create' ? `
                    <!-- Compact: Title and Badges in one line -->
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <${titleSize} class="card-title mb-0 me-2">${title}</${titleSize}>
                        <div class="d-flex gap-1 flex-wrap">
                            ${difficultyBadge}
                            ${muscleBadge}
                            ${equipmentBadge}
                        </div>
                    </div>
                    ${actionButtons}
                    ` : `
                    <!-- Regular: Title and Badges separated -->
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <${titleSize} class="card-title mb-0">${title}</${titleSize}>
                        <div class="d-flex flex-column gap-1 align-items-end">
                            ${difficultyBadge}
                            ${muscleBadge}
                            ${equipmentBadge}
                        </div>
                    </div>
                    ${description}
                    ${actionButtons}
                    `}
                </div>
            </div>
        `;
    }

    bindVideoEvents() {
        // Re-bind video modal events for dynamically created content
        document.querySelectorAll('.view-video-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const title = this.dataset.exerciseTitle;
                const maleFront = this.dataset.maleFront;
                const maleSide = this.dataset.maleSide;
                const femaleFront = this.dataset.femaleFront;
                const femaleSide = this.dataset.femaleSide;

                if (typeof openVideoModal === 'function') {
                    window.currentMaleVideos = { front: maleFront, side: maleSide };
                    window.currentFemaleVideos = { front: femaleFront, side: femaleSide };
                    openVideoModal(title);
                }
            });
        });
    }

    renderEmptyState() {
        const container = document.querySelector(this.containerSelector);
        const hasFilters = Object.values(this.currentFilters).some(value => value);

        container.innerHTML = `
            <div class="text-center py-12">
                <h2 class="text-2xl text-muted mb-4">No exercises found</h2>
                ${hasFilters ? `
                    <p class="text-muted mb-4">Try adjusting your search criteria.</p>
                    <button class="btn btn-primary" onclick="exerciseFilter.clearAllFilters()">
                        Clear Filters
                    </button>
                ` : '<p class="text-muted">Check back later for more exercises!</p>'}
            </div>
        `;
    }

    updateCount(count) {
        const countElement = document.querySelector(this.countSelector);
        if (countElement) {
            const hasFilters = Object.values(this.currentFilters).some(value => value);
            let message;

            if (hasFilters) {
                message = `${count} exercise${count !== 1 ? 's' : ''} (filtered)`;
            } else {
                message = `Showing ${count} popular exercises <small class="text-warning">(Use filters to find more)</small>`;
            }

            countElement.innerHTML = message;
        }
    }

    showLoading(show) {
        const loadingElement = document.querySelector(this.loadingSelector);
        if (loadingElement) {
            loadingElement.style.display = show ? 'block' : 'none';
        }

        // Add loading class to container
        const container = document.querySelector(this.containerSelector);
        if (container) {
            if (show) {
                container.classList.add('loading');
            } else {
                container.classList.remove('loading');
            }
        }
    }

    showError(message) {
        const container = document.querySelector(this.containerSelector);
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <h4 class="alert-heading">Error</h4>
                    <p>${message}</p>
                    <button class="btn btn-outline-danger" onclick="exerciseFilter.fetchExercises()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    clearAllFilters() {
        console.log('AJAX Filters: Clearing all filters');
        this.currentFilters = {
            search: '',
            muscle_group: '',
            equipment: '',
            difficulty: ''
        };
        this.updateFormElements();
        this.updateUrl();
        this.fetchExercises();
    }

    truncateText(text, wordLimit) {
        const words = text.split(' ');
        if (words.length <= wordLimit) return text;
        return words.slice(0, wordLimit).join(' ') + '...';
    }
}

// Global variable for the filter instance
let exerciseFilter;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('AJAX Filters: Initializing...');

    // Auto-detect page type
    const pageType = document.querySelector('#routine-exercises') ? 'routine_create' : 'list';
    console.log('AJAX Filters: Detected page type:', pageType);

    exerciseFilter = new ExerciseFilter({
        pageType: pageType,
        countSelector: pageType === 'routine_create' ? '.results-count' : '.results-count'
    });

    // Make it globally accessible
    window.exerciseFilter = exerciseFilter;
    console.log('AJAX Filters: Initialized successfully');
});