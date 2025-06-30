// Main JavaScript for Cellular Network Manager
document.addEventListener('DOMContentLoaded', function() {
    console.log('Multi-Store Management System initialized');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-refresh dashboard data every 5 minutes
    if (window.location.pathname === '/dashboard' || window.location.pathname === '/') {
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                location.reload();
            }
        }, 300000); // 5 minutes
    }
    
    // Confirm delete actions
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-btn') || e.target.closest('.delete-btn')) {
            if (!confirm('Sei sicuro di voler eliminare questo elemento?')) {
                e.preventDefault();
                return false;
            }
        }
    });
    
    // Loading state for forms
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Salvando...';
        }
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.classList.contains('alert-success')) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 500);
            }
        });
    }, 5000);
    
    // Service Worker registration (for future PWA features)
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed: ', error);
            });
    }
    
    // Page visibility API for pausing/resuming updates
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('Page hidden - pausing updates');
        } else {
            console.log('Page visible - resuming updates');
        }
    });
});