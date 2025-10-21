// 🌓 Theme Management System
// Universal theme switcher for all dashboards

(function() {
    'use strict';

    // Initialize theme on page load
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Create theme toggle button if it doesn't exist
        if (!document.querySelector('.theme-toggle')) {
            createThemeToggle();
        }
        
        updateThemeIcon(savedTheme);
    }

    // Create theme toggle button
    function createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';
        
        toggle.addEventListener('click', toggleTheme);
        
        // Add to top-bar-actions instead of body
        const topBarActions = document.querySelector('.top-bar-actions');
        if (topBarActions) {
            topBarActions.appendChild(toggle);
        } else {
            document.body.appendChild(toggle);
        }
    }

    // Toggle between light and dark themes
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Add transition animation
        document.documentElement.style.transition = 'all 0.3s ease';
        
        // Change theme
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        updateThemeIcon(newTheme);
        
        // Remove transition after animation
        setTimeout(() => {
            document.documentElement.style.transition = '';
        }, 300);
        
        // Show notification
        showThemeNotification(newTheme);
    }

    // Update theme toggle icon
    function updateThemeIcon(theme) {
        const toggle = document.querySelector('.theme-toggle');
        if (!toggle) return;
        
        const icon = toggle.querySelector('i');
        if (!icon) return;
        
        if (theme === 'dark') {
            icon.className = 'bi bi-sun-fill';
        } else {
            icon.className = 'bi bi-moon-stars-fill';
        }
    }

    // Show theme change notification
    function showThemeNotification(theme) {
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.innerHTML = `
            <i class="bi bi-${theme === 'dark' ? 'moon-stars-fill' : 'sun-fill'}"></i>
            <span>${theme === 'dark' ? 'Темная тема' : 'Светлая тема'}</span>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            background: ${theme === 'dark' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'};
            color: white;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: slideInRight 0.3s ease-out;
            z-index: 10000;
            pointer-events: none;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Add theme animation styles
    function addThemeStyles() {
        if (document.getElementById('theme-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'theme-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
            
            /* Smooth theme transitions */
            *:not(.theme-toggle):not(.theme-toggle *) {
                transition: background-color 0.3s ease, 
                           color 0.3s ease, 
                           border-color 0.3s ease,
                           box-shadow 0.3s ease !important;
            }
            
            /* Preserve animations and theme button */
            *:is([class*="animate"], [class*="animation"], .theme-toggle, .theme-toggle *) {
                transition: none !important;
            }
            
            /* Restore theme button transitions */
            .theme-toggle {
                transition: all 0.3s ease !important;
            }
            
            .theme-toggle i {
                transition: all 0.3s ease !important;
            }
        `;
        
        document.head.appendChild(style);
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            addThemeStyles();
            initTheme();
        });
    } else {
        addThemeStyles();
        initTheme();
    }

    // Export for manual initialization if needed
    window.ThemeManager = {
        init: initTheme,
        toggle: toggleTheme
    };
})();

