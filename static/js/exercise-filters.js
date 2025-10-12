// Shared exercise filtering functionality for both exercise list and routine create pages

// Debounce function for search input
let debounceTimer;
function debounceSubmit() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function() {
        const form = document.getElementById('exercise-filter-form');
        if (form) {
            form.submit();
        }
    }, 500);
}

// Badge filtering functionality
function initializeBadgeFiltering() {
    document.querySelectorAll('.clickable-badge').forEach(badge => {
        badge.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const filterType = this.dataset.filterType;
            const filterValue = this.dataset.filterValue;

            // Build URL with the filter parameter
            const url = new URL(window.location.href);

            if (filterType === 'difficulty') {
                url.searchParams.set('difficulty', filterValue);
            } else if (filterType === 'muscle') {
                url.searchParams.set('muscle_group', filterValue);
            } else if (filterType === 'equipment') {
                url.searchParams.set('equipment', filterValue);
            }

            // Navigate to the filtered URL
            window.location.href = url.toString();
        });
    });
}

// Initialize shared filtering on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initializeBadgeFiltering();
});