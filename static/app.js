// Multi-Store Management System - Client-side JavaScript
// Provides enhanced user experience and interactive features

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeConfirmations();
    initializeFormValidation();
    initializeCharts();
    initializeDatePickers();
    initializeSearch();
    initializeNotifications();
    
    // Auto-hide alerts after 5 seconds
    autoHideAlerts();
    
    // Initialize responsive tables
    initializeResponsiveTables();
    
    // Initialize loading states
    initializeLoadingStates();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Enhanced confirmation dialogs
function initializeConfirmations() {
    const deleteButtons = document.querySelectorAll('form[onsubmit*="confirm"]');
    deleteButtons.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const confirmModal = createConfirmModal(
                'Confirm Deletion',
                'Are you sure you want to delete this item? This action cannot be undone.',
                'danger'
            );
            
            confirmModal.show();
            
            confirmModal._element.querySelector('.btn-danger').addEventListener('click', () => {
                confirmModal.hide();
                this.submit();
            });
        });
    });
}

// Create custom confirmation modal
function createConfirmModal(title, message, type = 'primary') {
    const modalHtml = `
        <div class="modal fade" id="confirmModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-${type}">Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('confirmModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    return new bootstrap.Modal(document.getElementById('confirmModal'));
}

// Form validation enhancements
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[method="POST"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus first invalid field
                const firstInvalid = this.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            this.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                this.classList.add('was-validated');
            });
        });
    });
}

// Chart enhancements and animations
function initializeCharts() {
    // Set global Chart.js defaults for dark theme
    if (typeof Chart !== 'undefined') {
        Chart.defaults.color = '#ffffff';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        
        // Add animation to existing charts
        Chart.defaults.animation = {
            duration: 1000,
            easing: 'easeOutQuart'
        };
        
        // Responsive options
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
    }
}

// Enhanced date picker functionality
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        // Set reasonable min/max dates
        if (!input.min && input.name.includes('start')) {
            input.min = new Date().toISOString().split('T')[0];
        }
        
        // Auto-adjust end dates based on start dates
        if (input.name.includes('start')) {
            input.addEventListener('change', function() {
                const endInput = document.querySelector(`input[name*="end"]`);
                if (endInput && endInput.value && endInput.value < this.value) {
                    endInput.value = this.value;
                }
                if (endInput) {
                    endInput.min = this.value;
                }
            });
        }
    });
}

// Enhanced search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[name="search"]');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Debounce search to avoid too many requests
            searchTimeout = setTimeout(() => {
                const form = this.closest('form');
                if (form && this.value.length >= 2) {
                    // Add visual feedback
                    this.classList.add('searching');
                    
                    // Auto-submit after 500ms delay
                    setTimeout(() => {
                        form.submit();
                    }, 100);
                }
            }, 500);
        });
        
        // Clear search functionality
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                this.closest('form').submit();
            }
        });
    });
}

// Notification system
function initializeNotifications() {
    // Check for contract expiry notifications
    checkContractNotifications();
    
    // Check for goal achievements
    checkGoalNotifications();
}

function checkContractNotifications() {
    const expiringRows = document.querySelectorAll('.table-warning');
    if (expiringRows.length > 0) {
        showNotification(
            `${expiringRows.length} contract(s) expiring soon`,
            'warning',
            5000
        );
    }
}

function checkGoalNotifications() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const percentage = parseFloat(bar.style.width);
        if (percentage >= 100) {
            const goalName = bar.closest('.mb-3').querySelector('span').textContent;
            showNotification(
                `Goal achieved: ${goalName}!`,
                'success',
                7000
            );
        }
    });
}

function showNotification(message, type = 'info', duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show notification-alert" role="alert">
            <i class="fas fa-${getIconForType(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-hide after duration
    setTimeout(() => {
        const alert = document.querySelector('.notification-alert');
        if (alert) {
            bootstrap.Alert.getOrCreateInstance(alert).close();
        }
    }, duration);
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'danger': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Auto-hide alerts
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.notification-alert)');
    
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) return;
        
        setTimeout(() => {
            if (alert.parentNode) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    });
}

// Responsive table enhancements
function initializeResponsiveTables() {
    const tables = document.querySelectorAll('.table-responsive table');
    
    tables.forEach(table => {
        // Add scroll indicators
        const wrapper = table.parentElement;
        
        function updateScrollIndicators() {
            const scrollLeft = wrapper.scrollLeft;
            const scrollWidth = wrapper.scrollWidth;
            const clientWidth = wrapper.clientWidth;
            
            wrapper.classList.toggle('scroll-left', scrollLeft > 0);
            wrapper.classList.toggle('scroll-right', scrollLeft + clientWidth < scrollWidth);
        }
        
        wrapper.addEventListener('scroll', updateScrollIndicators);
        window.addEventListener('resize', updateScrollIndicators);
        updateScrollIndicators();
    });
}

// Loading states for forms and buttons
function initializeLoadingStates() {
    const forms = document.querySelectorAll('form[method="POST"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
                }, 10000);
            }
        });
    });
    
    // Store original button text
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(btn => {
        btn.dataset.originalText = btn.innerHTML;
    });
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

function debounce(func, wait) {
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

// Export functions for global use
window.MultiStoreManagement = {
    showNotification,
    createConfirmModal,
    formatCurrency,
    formatDate,
    debounce
};

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + / for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear modals and forms
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            bootstrap.Modal.getInstance(activeModal).hide();
        }
    }
    
    // Ctrl/Cmd + N for new item (where applicable)
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        const newButton = document.querySelector('a[href*="/new"]');
        if (newButton) {
            e.preventDefault();
            newButton.click();
        }
    }
});

// Page visibility API for pausing/resuming updates
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause any polling or updates
        console.log('Page hidden - pausing updates');
    } else {
        // Page is visible, resume updates
        console.log('Page visible - resuming updates');
    }
});

// Service Worker registration for offline support (if available)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

console.log('Multi-Store Management System initialized');
