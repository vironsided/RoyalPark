// User Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    checkAuth();

    // Initialize sidebar toggle
    initSidebarToggle();

    // Initialize navigation
    initNavigation();

    // Add animations
    addCardAnimations();
    addRippleEffect();
});

// Check if user is authenticated and has user role
function checkAuth() {
    const authToken = localStorage.getItem('authToken');
    const userRole = localStorage.getItem('userRole');

    if (!authToken || userRole !== 'user') {
        window.location.href = '/login.html';
        return;
    }

    // Set user info
    const username = localStorage.getItem('username') || 'Пользователь';
    const userNameEl = document.querySelector('.user-name');
    const userAvatarEl = document.querySelector('.user-avatar');
    
    if (userNameEl) {
        userNameEl.textContent = username;
    }
    
    if (userAvatarEl) {
        userAvatarEl.textContent = username.substring(0, 2).toUpperCase();
    }
}

// Sidebar toggle functionality
function initSidebarToggle() {
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle collapsed class
            sidebar.classList.toggle('collapsed');
            
            // Save state
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            
            // Update button icon rotation
            if (isCollapsed) {
                toggleBtn.style.transform = 'rotate(180deg)';
            } else {
                toggleBtn.style.transform = 'rotate(0deg)';
            }
        });

        // Restore sidebar state on page load
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            toggleBtn.style.transform = 'rotate(180deg)';
        }
    }

    // ESC key to toggle sidebar
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar) {
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            
            if (toggleBtn) {
                toggleBtn.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        }
    });
    
    // Close sidebar on outside click (mobile)
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 768 && sidebar) {
            if (!sidebar.contains(e.target) && !e.target.closest('.toggle-sidebar')) {
                sidebar.classList.add('collapsed');
            }
        }
    });
}

// Navigation functionality
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        if (item.hasAttribute('data-user-route')) {
            return;
        }

        item.addEventListener('click', function(e) {
            // Remove active class from all items
            navItems.forEach(navItem => navItem.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');

            // Get the href and load corresponding content
            const href = this.getAttribute('href');
            const isAnchorLink = !href || href.startsWith('#');

            if (isAnchorLink) {
                e.preventDefault();
                console.log('Loading section:', href);
            } else {
                // Allow default navigation for full links
                console.log('Navigating to:', href);
            }
        });
    });
}

// Add entrance animations to cards
function addCardAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all cards
    const cards = document.querySelectorAll('.stat-card, .chart-card, .activity-card, .card');
    cards.forEach(card => {
        observer.observe(card);
    });
}

// Add ripple effect to buttons
function addRippleEffect() {
    const buttons = document.querySelectorAll('.nav-item, .action-button');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
}


// Logout functionality
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    window.location.href = '/login.html';
}

// Add logout button event listener
document.addEventListener('click', function(e) {
    if (e.target.closest('.logout-btn')) {
        logout();
    }
});

// Add CSS for ripple effect dynamically
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    .action-button, .nav-item {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(rippleStyle);

console.log('📱 User dashboard loaded!');
