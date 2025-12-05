// 🌓 Theme Management System
// Universal theme switcher for all dashboards

(function() {
    'use strict';

    // Initialize theme on page load
    function initTheme() {
        // Default to dark theme if user hasn't chosen anything yet
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Проверяем, находимся ли мы в админ-панели
        const isAdminPanel = window.location.pathname.includes('/admin') || 
                            document.querySelector('.admin-container') ||
                            document.querySelector('#spa-content');
        
        // В админ-панели удаляем кнопку переключения темы, если она существует
        if (isAdminPanel) {
            const existingToggle = document.querySelector('.theme-toggle');
            if (existingToggle) {
                existingToggle.remove();
            }
            // Устанавливаем темную тему и фиксируем её
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            return; // Не создаем кнопку в админ-панели
        }
        
        // Для других страниц создаем кнопку, если её нет
        if (!document.querySelector('.theme-toggle')) {
            createThemeToggle();
            updateThemeIcon(savedTheme);
        }
    }

    // Create theme toggle button
    function createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.innerHTML = `
            <svg class="theme-icon-dark" style="display:none;" width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
            <svg class="theme-icon-light" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="4"></circle>
                <line x1="12" y1="2" x2="12" y2="4"></line>
                <line x1="12" y1="20" x2="12" y2="22"></line>
                <line x1="2" y1="12" x2="4" y2="12"></line>
                <line x1="20" y1="12" x2="22" y2="12"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
        `;
        
        toggle.addEventListener('click', toggleTheme);
        
        // Add to top-bar-actions instead of body
        const topBarActions = document.querySelector('.top-bar-actions');
        if (topBarActions) {
            // В user‑/accountant‑/maintenance‑кабинетах ставим переключатель
            // перед блоком профиля, чтобы порядок был:
            // поиск → уведомления → тема → язык → профиль
            const profile = topBarActions.querySelector('.user-profile');
            if (profile) {
                topBarActions.insertBefore(toggle, profile);
            } else {
                topBarActions.appendChild(toggle);
            }
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
        const sun = toggle.querySelector('.theme-icon-light');
        const moon = toggle.querySelector('.theme-icon-dark');
        if (!sun || !moon) return;
        if (theme === 'dark') {
            // show moon icon (indicates we are in dark, clicking will go to light)
            moon.style.display = 'block';
            sun.style.display = 'none';
        } else {
            moon.style.display = 'none';
            sun.style.display = 'block';
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

