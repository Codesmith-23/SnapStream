document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Auto-Dismiss Flash Messages
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.5s ease';
                setTimeout(() => alert.remove(), 500);
            });
        }, 4000); // Disappear after 4 seconds
    }

    // 2. Global Drag & Drop Prevention (Optional)
    // Prevents browser from opening files dropped outside the drop zone
    window.addEventListener('dragover', function(e) {
        e.preventDefault();
    }, false);
    
    window.addEventListener('drop', function(e) {
        e.preventDefault();
    }, false);

});