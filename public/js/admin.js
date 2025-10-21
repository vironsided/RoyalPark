// Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    checkAuth();

    // Initialize sidebar toggle
    initSidebarToggle();

    // Initialize navigation - DISABLED to allow normal page navigation
    // initNavigation();

    // Initialize charts
    initCharts();

    // Load dashboard data
    loadDashboardData();
    
    // Add modern animations and effects
    addCardAnimations();
    initSmoothScroll();
    addRippleEffect();
    
    // Add loading complete class for animations
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
});

// Check if user is authenticated and has admin role
function checkAuth() {
    // DISABLED - allow access without authentication for development
    // const authToken = localStorage.getItem('authToken');
    // const userRole = localStorage.getItem('userRole');

    // if (!authToken || userRole !== 'admin') {
    //     window.location.href = '/';
    //     return;
    // }

    // Set user info
    const username = localStorage.getItem('username') || 'Admin';
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
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all items
            navItems.forEach(navItem => navItem.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');

            // Get the href and load corresponding content
            const href = this.getAttribute('href');
            loadContent(href);
        });
    });
}

// Load content based on navigation
function loadContent(section) {
    console.log('Loading section:', section);
    
    // Update page title
    const pageTitle = document.querySelector('.page-title h1');
    const breadcrumb = document.querySelector('.breadcrumb-item:last-child');
    
    const sectionNames = {
        '#dashboard': 'Панель управления',
        '#analytics': 'Аналитика',
        '#reports': 'Отчеты',
        '#users': 'Пользователи',
        '#buildings': 'Здания',
        '#apartments': 'Квартиры',
        '#meters': 'Счетчики',
        '#payments': 'Платежи',
        '#invoices': 'Счета',
        '#debts': 'Задолженности',
        '#maintenance': 'Заявки на ремонт',
        '#inspections': 'Проверки',
        '#staff': 'Персонал',
        '#settings': 'Настройки',
        '#logs': 'Логи',
        '#backup': 'Резервное копирование'
    };

    if (pageTitle && sectionNames[section]) {
        pageTitle.textContent = sectionNames[section];
    }
    
    if (breadcrumb && sectionNames[section]) {
        breadcrumb.textContent = sectionNames[section];
    }

    // TODO: Load actual content from FastAPI backend
    // This will be connected to your backend API
}

// Initialize charts with Chart.js
function initCharts() {
    // Chart buttons
    const chartBtns = document.querySelectorAll('.chart-btn');
    
    chartBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            chartBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update chart data based on selected period
            console.log('Chart period changed to:', this.textContent);
            updateChartData(this.textContent);
        });
    });

    // Initialize Chart.js
    initPaymentChart();
}

// Create a beautiful gradient chart
function initPaymentChart() {
    const chartPlaceholder = document.querySelector('.chart-placeholder');
    
    if (!chartPlaceholder) return;
    
    // Replace placeholder with canvas
    const canvas = document.createElement('canvas');
    canvas.id = 'paymentChart';
    canvas.style.maxHeight = '300px';
    chartPlaceholder.innerHTML = '';
    chartPlaceholder.appendChild(canvas);
    chartPlaceholder.style.background = 'transparent';
    
    const ctx = canvas.getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
    gradient.addColorStop(1, 'rgba(118, 75, 162, 0.1)');
    
    // Sample data
    const data = {
        labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
        datasets: [{
            label: 'Платежи',
            data: [12000, 19000, 15000, 25000, 22000, 18000, 24000],
            backgroundColor: gradient,
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#fff',
            pointBorderColor: 'rgba(102, 126, 234, 1)',
            pointBorderWidth: 3,
            pointRadius: 5,
            pointHoverRadius: 7,
            pointHoverBackgroundColor: 'rgba(102, 126, 234, 1)',
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 3
        }]
    };
    
    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '₼' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        callback: function(value) {
                            return '₼' + value.toLocaleString();
                        },
                        color: '#6c757d'
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    };
    
    window.paymentChart = new Chart(ctx, config);
}

// Update chart data based on period
function updateChartData(period) {
    if (!window.paymentChart) return;
    
    let newData, newLabels;
    
    if (period === 'Неделя') {
        newLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
        newData = [12000, 19000, 15000, 25000, 22000, 18000, 24000];
    } else if (period === 'Месяц') {
        newLabels = ['Нед 1', 'Нед 2', 'Нед 3', 'Нед 4'];
        newData = [85000, 92000, 88000, 95000];
    } else if (period === 'Год') {
        newLabels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        newData = [320000, 340000, 330000, 360000, 350000, 380000, 390000, 370000, 385000, 395000, 400000, 420000];
    }
    
    window.paymentChart.data.labels = newLabels;
    window.paymentChart.data.datasets[0].data = newData;
    window.paymentChart.update('active');
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // TODO: Fetch data from FastAPI backend
        // const response = await fetch('FASTAPI_URL/api/dashboard/stats', {
        //     headers: {
        //         'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        //     }
        // });
        // const data = await response.json();
        
        // For now, using placeholder data
        console.log('Dashboard data loaded');
        
        // Update stats with real data when backend is ready
        updateStats({
            totalUsers: 1245,
            totalBuildings: 48,
            monthlyPayments: 2400000,
            activeRequests: 23
        });

    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Update statistics with animated counters
function updateStats(data) {
    console.log('Updating stats with:', data);
    
    // Animate counter numbers
    animateValue('.stat-card:nth-child(1) .stat-value', 0, data.totalUsers, 2000);
    animateValue('.stat-card:nth-child(2) .stat-value', 0, data.totalBuildings, 2000);
    animateValue('.stat-card:nth-child(4) .stat-value', 0, data.activeRequests, 2000);
}

// Animate counter from start to end
function animateValue(selector, start, end, duration) {
    const element = document.querySelector(selector);
    if (!element) return;
    
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        
        // Format number with separators
        const formatted = Math.floor(current).toLocaleString('ru-RU');
        element.textContent = formatted;
    }, 16);
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

// Add smooth scroll behavior
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#' || !href) return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Add ripple effect to buttons
function addRippleEffect() {
    const buttons = document.querySelectorAll('.nav-item, .chart-btn, button');
    
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
    
    button, .nav-item, .chart-btn {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(rippleStyle);

// Logout functionality
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    window.location.href = '/';
}

// Add logout button event listener
document.addEventListener('click', function(e) {
    if (e.target.closest('.logout-btn')) {
        logout();
    }
});

// Search functionality
const searchInput = document.querySelector('.search-box input');
if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        console.log('Searching for:', searchTerm);
        
        // TODO: Implement search functionality
        // This will search through users, buildings, apartments, etc.
    });
}

// Notification button
const notificationBtn = document.querySelector('.notification-btn');
if (notificationBtn) {
    notificationBtn.addEventListener('click', function() {
        console.log('Show notifications');
        // TODO: Show notifications dropdown
    });
}

// Auto-refresh data every 30 seconds
setInterval(() => {
    loadDashboardData();
}, 30000);