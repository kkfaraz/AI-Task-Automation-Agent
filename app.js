/**
 * AI Study Planner - Frontend JavaScript
 * Handles UI interactions, API calls, and dynamic content updates
 */

class StudyPlannerApp {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
        this.startPeriodicUpdates();
    }

    bindEvents() {
        // Global event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.onDocumentReady();
        });

        // Form validation
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });

        // Dynamic content loading with improved delegation
        document.addEventListener('click', (e) => {
            const actionElement = e.target.closest('[data-action]');
            if (actionElement) {
                e.preventDefault(); // Prevent default behavior if needed
                const action = actionElement.dataset.action;
                const id = actionElement.dataset.id;
                console.log('Action triggered:', action, 'ID:', id); // Debug log
                this.handleAction(actionElement);
            }
        });

        // Auto-save for forms
        document.querySelectorAll('[data-autosave]').forEach(input => {
            input.addEventListener('input', this.debounce((e) => {
                this.autoSave(e.target);
            }, 1000));
        });
    }

    onDocumentReady() {
        // Initialize Feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        } else {
            console.warn('Feather icons library not loaded');
        }

        // Initialize tooltips
        this.initTooltips();
        
        // Update time displays
        this.updateTimeDisplays();
        
        // Check for notifications
        this.checkNotifications();
        
        // Initialize progress animations
        this.animateProgress();
        
        // Set up keyboard shortcuts
        this.initKeyboardShortcuts();
    }

    initializeComponents() {
        // Initialize Charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.initializeCharts();
        } else {
            this.showNotification('Chart.js not loaded. Progress charts may not display.', 'warning');
        }

        // Initialize date pickers
        this.initializeDatePickers();

        // Initialize drag and drop for schedule items
        this.initializeDragDrop();
    }

    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            if (!input.value && input.name.includes('start')) {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                input.value = tomorrow.toISOString().split('T')[0];
                
                const endDateInput = input.closest('form')?.querySelector('input[name="end_date"]');
                if (endDateInput) {
                    const endDate = new Date(tomorrow);
                    endDate.setDate(endDate.getDate() + 30);
                    endDateInput.value = endDate.toISOString().split('T')[0];
                    
                    input.addEventListener('change', () => {
                        const selectedStart = new Date(input.value);
                        const minEnd = new Date(selectedStart);
                        minEnd.setDate(minEnd.getDate() + 1);
                        endDateInput.min = minEnd.toISOString().split('T')[0];
                        if (new Date(endDateInput.value) <= selectedStart) {
                            const defaultEnd = new Date(selectedStart);
                            defaultEnd.setDate(defaultEnd.getDate() + 14);
                            endDateInput.value = defaultEnd.toISOString().split('T')[0];
                        }
                    });
                }
            }
        });
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.quickSave();
            }

            // Ctrl/Cmd + N for new subject
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                window.location.href = '/add-subjects';
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const modal = bootstrap.Modal.getInstance(openModal);
                    if (modal) modal.hide();
                }
            }
        });
    }

    handleAction(element) {
        const action = element.dataset.action;
        const id = element.dataset.id;

        switch (action) {
            case 'complete-session':
                console.log('Handling complete-session for ID:', id); // Debug log
                this.completeSession(id);
                break;
            case 'miss-session':
                console.log('Handling miss-session for ID:', id); // Debug log
                this.missSession(id);
                break;
            case 'reschedule-session':
                this.rescheduleSession(id);
                break;
            case 'fetch-content':
                this.fetchContent(id);
                break;
            case 'view-summary':
                this.viewSummary(id);
                break;
            case 'view-wikipedia':
                this.viewWikipedia(id);
                break;
            case 'toggle-subject':
                this.toggleSubject(id);
                break;
            default:
                console.warn(`Unknown action: ${action}`);
        }
    }

    completeSession(sessionId) {
        if (!sessionId) {
            console.error('No session ID provided for completeSession');
            this.showNotification('Invalid session ID', 'error');
            return;
        }

        const modal = document.getElementById('completeSessionModal');
        const form = document.getElementById('completeSessionForm');
        
        if (!modal || !form) {
            console.error('Modal or form not found for completeSession');
            this.showNotification('Unable to open session completion modal', 'error');
            return;
        }

        form.action = `/complete-session/${sessionId}`;
        const bsModal = new bootstrap.Modal(modal);
        if (bsModal) {
            bsModal.show();
        } else {
            console.error('Bootstrap Modal initialization failed');
            this.showNotification('Failed to initialize modal', 'error');
        }
    }

    missSession(sessionId) {
        if (!sessionId) {
            console.error('No session ID provided for missSession');
            this.showNotification('Invalid session ID', 'error');
            return;
        }

        const modal = document.getElementById('missSessionModal');
        const form = document.getElementById('missSessionForm');
        
        if (!modal || !form) {
            console.error('Modal or form not found for missSession');
            this.showNotification('Unable to open session miss modal', 'error');
            return;
        }

        form.action = `/miss-session/${sessionId}`;
        const bsModal = new bootstrap.Modal(modal);
        if (bsModal) {
            bsModal.show();
        } else {
            console.error('Bootstrap Modal initialization failed');
            this.showNotification('Failed to initialize modal', 'error');
        }
    }

    rescheduleSession(sessionId) {
        this.showNotification('Rescheduling is not yet implemented', 'warning');
        // TODO: Implement rescheduling logic with API call to /reschedule-session/${sessionId}
    }

    async fetchContent(chapterId) {
        if (!chapterId) return;

        const button = document.querySelector(`[data-action="fetch-content"][data-id="${chapterId}"]`);
        if (!button) return;

        const originalText = button.innerHTML;
        const originalDisabled = button.disabled;

        try {
            button.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Fetching...';
            button.disabled = true;
            button.classList.add('loading');

            const response = await fetch(`/fetch-content/${chapterId}`);
            
            if (response.ok) {
                this.showNotification('Content fetched successfully!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error('Failed to fetch content');
            }
        } catch (error) {
            console.error('Error fetching content:', error);
            this.showNotification('Failed to fetch content. Please try again.', 'error');
            button.innerHTML = originalText;
            button.disabled = originalDisabled;
            button.classList.remove('loading');
        }
    }

    viewSummary(chapterId) {
        const chaptersData = window.chaptersData || [];
        const chapter = chaptersData.find(c => c.id === parseInt(chapterId));
        if (chapter && chapter.summary) {
            const summaryContent = document.getElementById('summaryContent');
            if (summaryContent) {
                summaryContent.innerHTML = `
                    <h6>${chapter.title}</h6>
                    <p class="text-muted">${chapter.subject_name}</p>
                    <hr>
                    <div style="white-space: pre-wrap;">${chapter.summary}</div>
                `;
                const modal = new bootstrap.Modal(document.getElementById('summaryModal'));
                modal.show();
            } else {
                this.showNotification('Unable to load summary content', 'error');
            }
        } else {
            this.showNotification('No summary available for this chapter', 'warning');
        }
    }

    viewWikipedia(chapterId) {
        const chaptersData = window.chaptersData || [];
        const chapter = chaptersData.find(c => c.id === parseInt(chapterId));
        if (chapter && chapter.wikipedia_content) {
            const wikipediaContent = document.getElementById('wikipediaContent');
            if (wikipediaContent) {
                wikipediaContent.innerHTML = `
                    <h6>${chapter.title}</h6>
                    <p class="text-muted">${chapter.subject_name}</p>
                    <hr>
                    <div>${chapter.wikipedia_content}</div>
                `;
                const modal = new bootstrap.Modal(document.getElementById('wikipediaModal'));
                modal.show();
            } else {
                this.showNotification('Unable to load Wikipedia content', 'error');
            }
        } else {
            this.showNotification('No Wikipedia content available for this chapter', 'warning');
        }
    }

    toggleSubject(subjectId) {
        this.showNotification('Subject toggling is not yet implemented', 'warning');
        // TODO: Implement subject toggling logic with API call
    }

    updateTimeDisplays() {
        const timeElements = document.querySelectorAll('[data-time]');
        timeElements.forEach(element => {
            const timestamp = element.dataset.time;
            if (timestamp) {
                const date = new Date(timestamp);
                const now = new Date();
                const diffMs = now - date;
                const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

                let displayText;
                if (diffDays === 0) {
                    displayText = 'Today';
                } else if (diffDays === 1) {
                    displayText = 'Yesterday';
                } else if (diffDays > 0) {
                    displayText = `${diffDays} days ago`;
                } else {
                    displayText = `In ${Math.abs(diffDays)} days`;
                }
                
                element.textContent = displayText;
                element.title = date.toLocaleString();
            }
        });
    }

    animateProgress() {
        const progressBars = document.querySelectorAll('.progress-bar');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const progressBar = entry.target;
                    const targetWidth = progressBar.style.width;
                    progressBar.style.width = '0%';
                    setTimeout(() => {
                        progressBar.style.width = targetWidth;
                    }, 100);
                    observer.unobserve(progressBar);
                }
            });
        });

        progressBars.forEach(bar => observer.observe(bar));
    }

    checkNotifications() {
        const upcomingSessions = document.querySelectorAll('.session-card[data-date]');
        const today = new Date().toISOString().split('T')[0];
        
        upcomingSessions.forEach(session => {
            const sessionDate = session.dataset.date;
            if (sessionDate === today) {
                session.classList.add('today');
                this.addNotificationBadge(session, 'Today');
            } else if (sessionDate < today) {
                session.classList.add('overdue');
                this.addNotificationBadge(session, 'Overdue');
            }
        });
    }

    addNotificationBadge(element, text) {
        if (element.querySelector('.notification-badge')) return;

        const badge = document.createElement('span');
        badge.className = 'badge bg-warning notification-badge';
        badge.textContent = text;
        element.style.position = 'relative';
        element.appendChild(badge);
    }

    startPeriodicUpdates() {
        setInterval(() => {
            this.updateTimeDisplays();
        }, 60000);
        setInterval(() => {
            this.checkNotifications();
        }, 300000);
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.markFieldError(field, 'This field is required');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        const dateFields = form.querySelectorAll('input[type="date"]');
        if (dateFields.length >= 2) {
            const startDate = new Date(dateFields[0].value);
            const endDate = new Date(dateFields[1].value);
            
            if (endDate <= startDate) {
                this.markFieldError(dateFields[1], 'End date must be after start date');
                isValid = false;
            }
        }

        return isValid;
    }

    markFieldError(field, message) {
        field.classList.add('is-invalid');
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    showNotification(message, type = 'info') {
        const alertClass = type === 'error' ? 'alert-danger' : 
                          type === 'success' ? 'alert-success' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';

        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alert);

        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    autoSave(input) {
        const form = input.closest('form');
        if (!form || !form.dataset.autosave) return;

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        localStorage.setItem(`autosave_${form.id}`, JSON.stringify({
            data,
            timestamp: Date.now()
        }));

        console.log('Auto-saved form data:', data);
    }

    quickSave() {
        const forms = document.querySelectorAll('form[data-autosave]');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                if (input.value) {
                    this.autoSave(input);
                }
            });
        });
        
        this.showNotification('Form data saved locally', 'success');
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    initializeCharts() {
        if (Chart.defaults) {
            Chart.defaults.color = getComputedStyle(document.documentElement)
                .getPropertyValue('--bs-body-color');
            Chart.defaults.borderColor = getComputedStyle(document.documentElement)
                .getPropertyValue('--bs-border-color');

            // Initialize progress chart if on progress page
            const progressChartCanvas = document.getElementById('progressChart');
            if (progressChartCanvas) {
                fetch('/api/progress-chart')
                    .then(response => response.json())
                    .then(data => {
                        this.createProgressChart(data);
                    })
                    .catch(error => {
                        console.error('Error loading chart data:', error);
                        this.showNotification('Failed to load progress chart data', 'error');
                    });
            }
        }
    }

    createProgressChart(data) {
        const ctx = document.getElementById('progressChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.by_subject.map(s => s.name),
                datasets: [{
                    label: 'Chapters Completed',
                    data: data.by_subject.map(s => s.completed),
                    backgroundColor: 'rgba(13, 202, 240, 0.8)',
                    borderColor: 'rgba(13, 202, 240, 1)',
                    borderWidth: 1
                }, {
                    label: 'Total Chapters',
                    data: data.by_subject.map(s => s.total),
                    backgroundColor: 'rgba(108, 117, 125, 0.3)',
                    borderColor: 'rgba(108, 117, 125, 0.8)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: 'var(--bs-body-color)'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'var(--bs-body-color)'
                        },
                        grid: {
                            color: 'var(--bs-border-color)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'var(--bs-body-color)'
                        },
                        grid: {
                            color: 'var(--bs-border-color)'
                        }
                    }
                }
            }
        });
    }

    initializeDragDrop() {
        const draggableItems = document.querySelectorAll('[draggable="true"]');
        
        draggableItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.id);
                item.classList.add('dragging');
            });

            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
            });
        });

        const dropZones = document.querySelectorAll('[data-drop-zone]');
        
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
                const itemId = e.dataTransfer.getData('text/plain');
                this.showNotification('Drag-and-drop reordering is not yet implemented', 'warning');
                // TODO: Implement drop logic with API call to reorder sessions
            });
        });
    }
}

// Utility functions
window.StudyPlannerUtils = {
    formatDuration(hours) {
        if (hours < 1) {
            return `${Math.round(hours * 60)} min`;
        } else if (hours === 1) {
            return '1 hour';
        } else {
            return `${hours} hours`;
        }
    },

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    getTimeUntilDeadline(deadlineString) {
        const deadline = new Date(deadlineString);
        const now = new Date();
        const diff = deadline - now;
        
        if (diff < 0) return 'Past due';
        
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (days > 0) {
            return `${days} day${days !== 1 ? 's' : ''} left`;
        } else if (hours > 0) {
            return `${hours} hour${hours !== 1 ? 's' : ''} left`;
        } else {
            return 'Due soon';
        }
    },

    calculateStudyProgress(completed, total) {
        if (total === 0) return 0;
        return Math.round((completed / total) * 100);
    }
};

// Initialize the app when the DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.studyPlannerApp = new StudyPlannerApp();
    });
} else {
    window.studyPlannerApp = new StudyPlannerApp();
}

// Global functions for backward compatibility
window.completeSession = function(sessionId) {
    if (window.studyPlannerApp) {
        window.studyPlannerApp.completeSession(sessionId);
    }
};

window.missSession = function(sessionId) {
    if (window.studyPlannerApp) {
        window.studyPlannerApp.missSession(sessionId);
    }
};

window.fetchContent = function(chapterId) {
    if (window.studyPlannerApp) {
        window.studyPlannerApp.fetchContent(chapterId);
    }
};