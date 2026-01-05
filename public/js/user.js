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

    // Setup action buttons
    setupActionButtons();

    // Quick initial UI update from cache
    const cachedUser = localStorage.getItem('userData');
    if (cachedUser) {
        try {
            window.updateUserHeader(JSON.parse(cachedUser));
        } catch(e) {}
    }

    // Load user profile for header (name and avatar) on all pages
    loadUserProfileForHeader();

    // Load dashboard data from backend (will be called after auth check)
    // Small delay to ensure auth check completes
    setTimeout(() => {
        loadDashboardData();
    }, 200);
});

// Check if user is authenticated and has RESIDENT role
async function checkAuth() {
    // Try to verify session with backend
    try {
        const response = await fetch(`${API_BASE_URL}/api/resident/dashboard`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Not authenticated - redirect to login
                window.location.href = '/login.html';
                return;
            }
            // For other errors, continue (might be temporary network issue)
            console.warn('Auth check returned status:', response.status);
        }

        // If we get here, user is authenticated (or network issue)
        // User info will be set by loadDashboardData()
        return;
    } catch (error) {
        console.error('Auth check error:', error);
        // Don't redirect on network errors, just log
        // User info will be loaded by loadUserProfileForHeader() and loadDashboardData()
        // Don't overwrite with localStorage data to avoid showing "Пользователь"
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
async function logout() {
    try {
        // Call backend logout endpoint to clear session
        await fetch(`${API_BASE_URL}/resident/logout`, {
            method: 'GET',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Clear localStorage
        localStorage.removeItem('authToken');
        localStorage.removeItem('userRole');
        localStorage.removeItem('username');
        // Redirect to login
        window.location.href = '/login.html';
    }
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

// API Configuration
if (typeof window.API_BASE_URL === 'undefined') {
    window.API_BASE_URL = window.BACKEND_API_BASE || 'http://localhost:8000';
}
const API_BASE_URL = window.API_BASE_URL;

// Store dashboard data globally
window.dashboardData = null;

// Update user name and avatar in header (available globally for all pages)
window.updateUserHeader = function updateUserHeader(userData) {
    if (!userData) return;
    
    const userNameEl = document.querySelector('.user-name');
    const userAvatarEl = document.querySelector('.user-avatar');
    
    // Determine the best name to show
    // Priority: full_name -> username -> current text (if not "Пользователь") -> fallback
    let fullName = userData.full_name || userData.username;
    
    if (!fullName && userNameEl) {
        const currentName = userNameEl.textContent.trim();
        if (currentName && currentName !== 'Пользователь' && currentName !== 'User') {
            fullName = currentName;
        }
    }
    
    if (!fullName) {
        fullName = 'Пользователь';
    }
    
    if (userNameEl) {
        userNameEl.textContent = fullName;
    }
    
    // Cache for quick initial load next time
    localStorage.setItem('userData', JSON.stringify(userData));
    
    if (userAvatarEl) {
        const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        
        if (userData.avatar_path) {
            // Create image object to check if it loads correctly
            const img = new Image();
            img.onload = function() {
                userAvatarEl.style.background = 'none';
                userAvatarEl.style.backgroundImage = `url('${API_BASE_URL}${userData.avatar_path}')`;
                userAvatarEl.style.backgroundSize = 'cover';
                userAvatarEl.style.backgroundPosition = 'center';
                userAvatarEl.style.backgroundRepeat = 'no-repeat';
                userAvatarEl.textContent = '';
            };
            img.onerror = function() {
                // If fails to load, fallback to initials and gradient
                userAvatarEl.style.background = '';
                userAvatarEl.style.backgroundImage = '';
                userAvatarEl.textContent = initials || fullName.substring(0, 2).toUpperCase();
            };
            img.src = `${API_BASE_URL}${userData.avatar_path}`;
        } else {
            userAvatarEl.style.background = ''; // Restore default gradient from CSS
            userAvatarEl.style.backgroundImage = '';
            userAvatarEl.textContent = initials || fullName.substring(0, 2).toUpperCase();
        }
    }
};

// Load user profile and update header (available globally)
window.loadUserProfileForHeader = async function loadUserProfileForHeader() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/users/me`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const user = await response.json();
            if (typeof window.updateUserHeader === 'function') {
                window.updateUserHeader(user);
                // Store user data globally to prevent overwriting with "Пользователь"
                window.currentUserData = user;
                // Cache for next initial load
                localStorage.setItem('userData', JSON.stringify(user));
            }
        }
    } catch (error) {
        console.error('Error loading user profile for header:', error);
    }
}

// Load dashboard data from backend
window.loadDashboardData = async function loadDashboardData() {
    const spaContent = document.getElementById('userSpaContent');
    const currentRoute = window.userSpaRouter?.currentRoute || 
                         (window.location.hash ? window.location.hash.replace('#', '').split('?')[0] : 'dashboard');
    const isDashboard = currentRoute === 'dashboard';
    
    // Show loading state ONLY if on dashboard
    if (spaContent && isDashboard) {
        // ... (rest of the code)
        spaContent.innerHTML = `
            <div class="loading-state" style="display:flex;align-items:center;justify-content:center;min-height:400px;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
            </div>
        `;
    }

    try {
        // Добавляем timestamp для предотвращения кэширования
        const timestamp = new Date().getTime();
        const response = await fetch(`${API_BASE_URL}/api/resident/dashboard?t=${timestamp}`, {
            method: 'GET',
            credentials: 'include', // Include cookies for session auth
            headers: {
                'Content-Type': 'application/json',
            },
            cache: 'no-cache' // Предотвращаем кэширование
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Unauthorized - redirect to login
                window.location.href = '/login.html';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        window.dashboardData = data; // Store globally for later use
        updateDashboardUI(data);
        
        // Load invoices for user's residents
        if (data.residents && data.residents.length > 0) {
            loadInvoices(data.residents.map(r => r.id));
        }
        
        // Load latest news
        loadDashboardNews();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Don't show error popup on network errors, just log
        // The page will still be usable with cached data if available
        if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION')) {
            console.warn('Network error - backend might be unavailable. Using cached data if available.');
        } else {
            showError('Не удалось загрузить данные. Проверьте подключение к серверу.');
        }
    }
}

// Update UI with dashboard data
function updateDashboardUI(data) {
    // Update user info in header (use global function)
    // Only update if we don't already have user data with full_name, or if data is different
    if (data.user) {
        // If we already have user data with full_name, don't overwrite it with data that might not have full_name
        if (window.currentUserData && window.currentUserData.full_name) {
            // We already have good data, only update if new data also has full_name and is different
            if (data.user.full_name && data.user.full_name !== window.currentUserData.full_name) {
                window.updateUserHeader(data.user);
                window.currentUserData = data.user;
            }
            // Otherwise, keep current data to prevent showing "Пользователь"
        } else {
            // No current data or current data doesn't have full_name, update with new data
            window.updateUserHeader(data.user);
            window.currentUserData = data.user;
        }
    }

    // Get container and template
    let container = document.getElementById('residentsContainer');
    let template = container?.querySelector('.resident-card-template');
    
    // Check if we are currently on the dashboard route
    // Use the router's current route if available, otherwise check the hash
    const currentRoute = window.userSpaRouter?.currentRoute || 
                         (window.location.hash ? window.location.hash.replace('#', '').split('?')[0] : 'dashboard');
    const isDashboard = currentRoute === 'dashboard';
    
    // If container not found (maybe showing loading state) AND we are on dashboard, restore it from SPA router
    if (isDashboard && (!container || !template)) {
        const spaContent = document.getElementById('userSpaContent');
        if (spaContent && window.userSpaRouter && window.userSpaRouter.routes.dashboard.content) {
            spaContent.innerHTML = window.userSpaRouter.routes.dashboard.content;
            container = document.getElementById('residentsContainer');
            template = container?.querySelector('.resident-card-template');
            
            // Re-apply translations to restored content
            if (window.i18n) {
                const savedLang = localStorage.getItem('language') || 'ru';
                window.i18n.applyLanguage(savedLang);
        }
        }
    }
    
    // If we are not on the dashboard page, just return (header is already updated above)
    if (!container || !template) {
        return;
    }

    // Remove all existing resident cards (except template)
    container.querySelectorAll('.resident-card:not(.resident-card-template)').forEach(card => card.remove());
    
    // Remove existing wrapper if exists
    const existingWrapper = container.querySelector('.residents-cards-wrapper');
    if (existingWrapper) {
        existingWrapper.remove();
    }

    // Update summary cards (use aggregate summary)
    const summary = data.summary || {};
    updateStatValue('.resident-summary-card:first-child .summary-value', summary.total_debt);
    updateStatValue('.resident-summary-card.accent .summary-value', summary.total_advance);

    // Create card for each resident
    if (data.residents && data.residents.length > 0) {
        const hasMultipleResidents = data.residents.length > 1;
        
        // Add class to container if multiple residents
        if (hasMultipleResidents) {
            container.classList.add('has-multiple-residents');
        } else {
            container.classList.remove('has-multiple-residents');
        }
        
        // Create wrapper for resident cards if multiple
        let residentsWrapper = null;
        if (hasMultipleResidents) {
            residentsWrapper = document.createElement('div');
            residentsWrapper.className = 'residents-cards-wrapper';
        }
        
        data.residents.forEach((resident, index) => {
            // Clone template
            const card = template.cloneNode(true);
            card.classList.remove('resident-card-template');
            card.style.display = '';
            
        // Update greeting (only show on first card)
        const greetingEl = card.querySelector('.resident-greeting');
        if (greetingEl && index === 0) {
            const displayName = data.user?.full_name || data.user?.username || (window.currentUserData?.full_name) || 'Пользователь';
            greetingEl.innerHTML = `<span data-i18n="user_greeting_prefix">Здравствуйте,</span> ${displayName}`;
        } else if (greetingEl) {
            greetingEl.style.display = 'none';
        }
            
            // Update resident tag
            const residentCodeVal = card.querySelector('.resident-code-val');
            if (residentCodeVal) {
                residentCodeVal.textContent = resident.code;
        }
        
            // Update payment deadline
            const dueDateEl = card.querySelector('.resident-due-date');
            if (dueDateEl) {
                if (resident.due_date) {
                    const dueDate = new Date(resident.due_date);
                    const formattedDate = dueDate.toLocaleDateString('ru-RU', { 
                        day: '2-digit', 
                        month: '2-digit', 
                        year: 'numeric' 
                    });
                    dueDateEl.textContent = `Срок оплаты: ${formattedDate}`;
                    dueDateEl.style.display = 'flex';
                    
                    // Apply styling based on due_state
                    dueDateEl.className = 'resident-due-date';
                    if (resident.due_state === 'over') {
                        dueDateEl.classList.add('due-over');
                    } else if (resident.due_state === 'soon') {
                        dueDateEl.classList.add('due-soon');
                    } else if (resident.due_state === 'ok') {
                        dueDateEl.classList.add('due-ok');
                    }
                } else {
                    dueDateEl.style.display = 'none';
                }
        }

        // Update month due
            const monthDueEl = card.querySelector('.resident-amount-box strong');
        if (monthDueEl) {
                monthDueEl.textContent = formatCurrency(resident.month_due);
        }

        // Update progress bar
            const progressBar = card.querySelector('.resident-progress-bar');
            const progressFill = card.querySelector('.resident-progress-fill');
            if (progressBar && progressFill) {
                const percentage = resident.month_total > 0 
                    ? (resident.month_paid / resident.month_total) * 100 
                : 0;
            progressFill.style.width = `${Math.min(percentage, 100)}%`;

                const paidShort = Math.round(resident.month_paid || 0);
                const totalShort = Math.round(resident.month_total || 0);
            let progressTextSpan = progressBar.querySelector('.resident-progress-text');
            if (!progressTextSpan) {
                progressTextSpan = document.createElement('span');
                progressTextSpan.className = 'resident-progress-text';
                progressBar.appendChild(progressTextSpan);
            }
            progressTextSpan.textContent = `${paidShort}/${totalShort}`;
        }

            // Update stats
            const statsRow = card.querySelector('.resident-stats-row');
            if (statsRow) {
                const debtEl = statsRow.querySelector('div:nth-child(1) .resident-stat-value');
                const advanceEl = statsRow.querySelector('div:nth-child(2) .resident-stat-value');
                const payNowEl = statsRow.querySelector('div:nth-child(3) .resident-stat-value');
                
                if (debtEl) {
                    debtEl.textContent = formatCurrency(resident.debt_total);
                }
                if (advanceEl) {
                    advanceEl.textContent = formatCurrency(resident.advance_total);
                    if (resident.advance_total > 0) {
                        advanceEl.classList.add('positive');
                    } else {
                        advanceEl.classList.remove('positive');
                    }
                }
                if (payNowEl) {
                    payNowEl.textContent = formatCurrency(resident.pay_now);
                }
                
                // Disable pay-from-advance button if no advance or no debt
                const payFromAdvanceBtn = card.querySelector('[data-action="pay-from-advance"]');
                if (payFromAdvanceBtn) {
                    const hasAdvance = resident.advance_total > 0;
                    const hasDebt = resident.pay_now > 0;
                    payFromAdvanceBtn.disabled = !hasAdvance || !hasDebt;
                    if (payFromAdvanceBtn.disabled) {
                        payFromAdvanceBtn.style.opacity = '0.5';
                        payFromAdvanceBtn.style.cursor = 'not-allowed';
                    } else {
                        payFromAdvanceBtn.style.opacity = '1';
                        payFromAdvanceBtn.style.cursor = 'pointer';
                    }
                }
            }
            
            // Set resident ID on all buttons
            const residentId = resident.id.toString();
            card.querySelectorAll('[data-resident-id]').forEach(btn => {
                btn.setAttribute('data-resident-id', residentId);
            });
            
            // Add card to wrapper or container
            if (hasMultipleResidents && residentsWrapper) {
                residentsWrapper.appendChild(card);
            } else {
                // Single resident - insert before side cards
                const sideCards = container.querySelector('.resident-side-cards');
                if (sideCards) {
                    container.insertBefore(card, sideCards);
                } else {
                    container.appendChild(card);
                }
            }
        });
        
        // Insert wrapper before side cards if multiple residents
        if (hasMultipleResidents && residentsWrapper) {
            const sideCards = container.querySelector('.resident-side-cards');
            if (sideCards) {
                container.insertBefore(residentsWrapper, sideCards);
            } else {
                container.appendChild(residentsWrapper);
            }
        }
        
        // Update stats grid cards
        updateStatsGrid(data);
    }
}

// Update stats grid cards with real data
function updateStatsGrid(data) {
    const summary = data.summary || {};
    
    // 1. Неоплаченных счета (Unpaid bills)
    const unpaidCountEl = document.getElementById('stat-unpaid-count');
    const unpaidStatusEl = document.getElementById('stat-unpaid-status');
    if (unpaidCountEl) {
        unpaidCountEl.textContent = (summary.unpaid_invoices_count || 0).toString();
    }
    if (unpaidStatusEl) {
        if (summary.unpaid_invoices_count > 0) {
            unpaidStatusEl.classList.add('negative');
            unpaidStatusEl.classList.remove('positive');
        } else {
            unpaidStatusEl.classList.remove('negative');
            unpaidStatusEl.classList.add('positive');
            unpaidStatusEl.textContent = 'Всё оплачено';
        }
    }
    
    // 2. Электричество (кВт⋅ч за месяц)
    const electricityEl = document.getElementById('stat-electricity');
    if (electricityEl) {
        electricityEl.textContent = Math.round(summary.monthly_kwh || 0).toString();
    }
    
    // 3. Вода (м³ за месяц)
    const waterEl = document.getElementById('stat-water');
    if (waterEl) {
        waterEl.textContent = (summary.monthly_water_m3 || 0).toFixed(1);
    }
    
    // 4. Газ (м³ за месяц)
    const gasEl = document.getElementById('stat-gas');
    if (gasEl) {
        gasEl.textContent = (summary.monthly_gas_m3 || 0).toFixed(1);
    }
}


// Load invoices from backend for specific residents
async function loadInvoices(residentIds) {
    if (!residentIds || residentIds.length === 0) {
        return;
    }

    try {
        // Fetch invoices for each resident and combine
        const allInvoices = [];
        
        for (const residentId of residentIds) {
            const response = await fetch(
                `${API_BASE_URL}/api/invoices?resident_id=${residentId}&per_page=10`,
                {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }
            );

            if (response.ok) {
                const data = await response.json();
                if (data.invoices) {
                    allInvoices.push(...data.invoices);
                }
            }
        }

        // Sort by period (newest first) and take top 5
        allInvoices.sort((a, b) => {
            if (a.period_year !== b.period_year) {
                return b.period_year - a.period_year;
            }
            return b.period_month - a.period_month;
        });

        updateInvoicesUI(allInvoices.slice(0, 5));
    } catch (error) {
        console.error('Error loading invoices:', error);
        // Don't show error for invoices, just log it
    }
}

// Update invoices UI
function updateInvoicesUI(invoices) {
    const billsList = document.querySelector('.bills-list');
    if (!billsList) return;

    // Clear existing bills (keep first few as template if needed)
    billsList.innerHTML = '';

    if (invoices.length === 0) {
        billsList.innerHTML = '<div class="text-center p-4 text-muted">Нет счетов</div>';
        return;
    }

    invoices.forEach(invoice => {
        const billItem = createBillItem(invoice);
        billsList.appendChild(billItem);
    });
}

// Create bill item element
function createBillItem(invoice) {
    const item = document.createElement('div');
    item.className = 'bill-item';

    const status = invoice.status;
    const isPaid = status === 'paid' || invoice.paid_amount >= invoice.amount_total;
    const isPending = status === 'issued' || status === 'partial';

    const iconClass = isPaid ? 'bill-paid' : 'bill-pending';
    const icon = isPaid ? 'bi-check-circle' : 'bi-receipt';
    const badgeClass = isPaid ? 'badge-success' : 'badge-warning';
    const badgeText = isPaid ? 'Оплачено' : 'К оплате';

    const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    const periodText = `${monthNames[invoice.period_month - 1]} ${invoice.period_year}`;

    item.innerHTML = `
        <div class="bill-icon ${iconClass}">
            <i class="bi ${icon}"></i>
        </div>
        <div class="bill-details">
            <div class="bill-title">Счёт #${invoice.number || invoice.id}</div>
            <div class="bill-date">${periodText}</div>
        </div>
        <div class="bill-amount">
            <div class="bill-sum">${formatCurrency(invoice.amount_total)}</div>
            <span class="badge ${badgeClass}">${badgeText}</span>
        </div>
    `;

    // Make clickable to open invoice print page
    item.style.cursor = 'pointer';
    item.addEventListener('click', () => {
        // Store invoice ID in sessionStorage for print page
        sessionStorage.setItem('printInvoiceId', invoice.id.toString());
        sessionStorage.setItem('currentInvoiceId', invoice.id.toString());
        // Open print page with invoice ID in URL
        window.open(`/user/invoice-print.html?id=${invoice.id}`, '_blank', 'noopener');
    });

    return item;
}

// Helper function to update stat value
// Accepts either a selector string or an element
function updateStatValue(selectorOrElement, value, isPositive = false) {
    const element = typeof selectorOrElement === 'string' 
        ? document.querySelector(selectorOrElement)
        : selectorOrElement;
    
    if (element) {
        element.textContent = formatCurrency(value);
        if (isPositive && value > 0) {
            element.classList.add('positive');
        } else if (value > 0) {
            element.classList.remove('positive');
        }
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Setup action buttons
function setupActionButtons() {
    // Все клики обрабатываем через делегирование
    document.addEventListener('click', async (e) => {
        // Нужны данные дашборда для сумм
        const summary = window.dashboardData?.summary || {};
        const residents = window.dashboardData?.residents || [];

        // "Погасить из аванса" (Pay from advance)
        const payFromAdvanceBtn = e.target.closest('[data-action="pay-from-advance"]');
        if (payFromAdvanceBtn) {
            e.preventDefault();
            const residentIdAttr = payFromAdvanceBtn.getAttribute('data-resident-id');
            if (residentIdAttr) {
                const residentId = parseInt(residentIdAttr, 10);
            await applyAdvance(residentId);
            }
            return;
        }

        // "Оплатить за месяц" — оплачиваем только текущий месяц для конкретного резидента
        const payMonthBtn = e.target.closest('[data-action="pay-month"]');
        if (payMonthBtn && window.dashboardData) {
            e.preventDefault();
            const residentIdAttr = payMonthBtn.getAttribute('data-resident-id');
            let amount = summary.total_month || 0;
            let residentCode = '';
            
            // Если есть resident_id, используем данные конкретного резидента
            if (residentIdAttr) {
                const residentId = parseInt(residentIdAttr, 10);
                const resident = residents.find(r => r.id === residentId);
                if (resident) {
                    amount = resident.month_due || 0;
                    residentCode = resident.code || '';
                }
            }
            
            startPaymentFlow('month', amount, summary, residentIdAttr ? parseInt(residentIdAttr, 10) : null, residentCode);
            return;
        }

        // "Оплатить всё" — полное погашение долга по всем счетам (агрегированная сумма)
        const payAllBtn = e.target.closest('[data-action="pay-all"]');
        if (payAllBtn && window.dashboardData) {
            e.preventDefault();
            const amount = summary.total_debt || 0;
            // Для "Оплатить всё" используем ID первого резидента как технический, 
            // так как backend требует resident_id для создания платежа.
            // При scope="all" backend сам найдет все остальные дома этого владельца.
            const firstResident = residents[0];
            const residentId = firstResident ? firstResident.id : null;
            startPaymentFlow('all', amount, summary, residentId, 'Все объекты');
            return;
        }
    });
}

// Запуск цепочки оплаты: сохраняем параметры и переходим на страницу оплаты
function startPaymentFlow(scope, amount, summaryFromDashboard, residentId = null, residentCode = null) {
    // Если residentCode не передан и это НЕ 'all', пытаемся получить из DOM
    if (!residentCode && scope !== 'all') {
        const residentCodeEl = document.querySelector('.resident-code-val');
        residentCode = residentCodeEl ? residentCodeEl.textContent.trim() : '';
    }
    
    // Для 'all' устанавливаем понятный заголовок, если он не передан
    if (scope === 'all' && (!residentCode || residentCode === '')) {
        residentCode = 'Все объекты';
    }

    // Человеко-понятный текст типа платежа
    let scopeLabel;
    if (scope === 'all') {
        scopeLabel = 'Полное погашение долга по счетам';
    } else {
        scopeLabel = 'Оплата счетов за текущий месяц';
    }

    // Сохраняем данные в sessionStorage, чтобы страница оплаты могла их использовать
    try {
        sessionStorage.setItem('paymentScope', scope);
        sessionStorage.setItem('paymentAmount', String(amount || 0));
        sessionStorage.setItem('paymentScopeLabel', scopeLabel);
        // Устанавливаем временную метку для валидации данных на странице оплаты
        sessionStorage.setItem('paymentTimestamp', String(Date.now()));
        if (summaryFromDashboard && typeof summaryFromDashboard === 'object') {
            sessionStorage.setItem('paymentSummary', JSON.stringify(summaryFromDashboard));
        }
        if (residentCode) {
            sessionStorage.setItem('paymentResidentCode', residentCode);
        }
        if (residentId) {
            sessionStorage.setItem('paymentResidentId', String(residentId));
        }
    } catch (err) {
        console.warn('Failed to store payment data in sessionStorage', err);
    }

    // Переходим на SPA-маршрут "report" (страница оплаты)
    if (window.userSpaRouter && typeof window.userSpaRouter.navigate === 'function') {
        window.userSpaRouter.navigate('report', true);
    } else {
        // fallback — обычный переход по URL
        window.location.href = '/user/dashboard.html#report';
    }
}

// Apply advance payment
// Apply advance payment
async function applyAdvance(residentId) {
    const confirmed = await showConfirm('Применить аванс к открытым счетам?', 'Подтверждение');
    if (!confirmed) {
        return;
    }

    try {
        const formData = new FormData();
        formData.append('resident_id', residentId);

        const response = await fetch(`${API_BASE_URL}/api/resident/apply-advance`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при применении аванса');
        }

        const result = await response.json();
        
        if (result.ok) {
            await showAlert(result.message, 'Успешно', 'success');
            // Reload data to reflect changes
            loadDashboardData();
        } else {
            throw new Error(result.error || 'Не удалось применить аванс');
        }
    } catch (error) {
        console.error('Error applying advance:', error);
        showAlert(error.message, 'Ошибка', 'error');
    }
}

// Modal confirmation dialog (returns Promise<boolean>)
window.showConfirm = function showConfirm(message, title = 'Подтвердите действие') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'user-modal-overlay';
        overlay.innerHTML = `
            <div class="user-confirm-modal">
                <div class="user-confirm-modal-header">
                    <div class="user-confirm-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                        </svg>
                    </div>
                    <h3>${title}</h3>
                    <button class="user-confirm-modal-close" type="button">&times;</button>
                </div>
                <div class="user-confirm-modal-body">
                    <p>${message}</p>
                </div>
                <div class="user-confirm-modal-footer">
                    <button class="user-btn user-btn-secondary btn-cancel" type="button">Отмена</button>
                    <button class="user-btn user-btn-primary btn-confirm" type="button">OK</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Show with animation
        setTimeout(() => overlay.classList.add('show'), 10);
        
        let resolved = false;
        const close = (result) => {
            if (resolved) return; // Prevent double resolution
            resolved = true;
            
            overlay.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(overlay)) {
                    document.body.removeChild(overlay);
                }
                resolve(result);
            }, 300);
        };
        
        // Get button references after DOM is ready
        const confirmBtn = overlay.querySelector('.btn-confirm');
        const cancelBtn = overlay.querySelector('.btn-cancel');
        const closeBtn = overlay.querySelector('.user-confirm-modal-close');
        
        // Add event listeners with proper handling
        if (confirmBtn) {
            confirmBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                close(true); // OK - подтверждаем действие
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                close(false); // Отмена - отменяем действие
            });
        }
        
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                close(false); // Закрытие = отмена
            });
        }
        
        // Close on overlay click (but not on modal content)
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                close(false); // Клик вне модалки = отмена
        }
        });
        
        // ESC key handler
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                close(false); // ESC = отмена
                document.removeEventListener('keydown', escHandler);
        }
        };
        document.addEventListener('keydown', escHandler);
    });
}

// Modal alert dialog
window.showAlert = function showAlert(message, title = 'Уведомление', type = 'info') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'user-modal-overlay';
        
        const iconMap = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const colorMap = {
            success: '#34c759',
            error: '#ff3b30',
            warning: '#ff9500',
            info: '#007aff'
        };
        
        overlay.innerHTML = `
            <div class="user-alert-modal">
                <div class="user-alert-modal-header">
                    <div class="user-alert-icon" style="background: ${colorMap[type]}20; color: ${colorMap[type]}">
                        ${iconMap[type] || iconMap.info}
                    </div>
                    <h3>${title}</h3>
                    <button class="user-alert-modal-close" type="button">&times;</button>
                </div>
                <div class="user-alert-modal-body">
                    <p>${message}</p>
                </div>
                <div class="user-alert-modal-footer">
                    <button class="user-btn user-btn-primary btn-ok" type="button">OK</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Show with animation
        setTimeout(() => overlay.classList.add('show'), 10);
        
        const close = () => {
            overlay.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(overlay);
                resolve();
            }, 300);
        };
        
        overlay.querySelector('.btn-ok').addEventListener('click', close);
        overlay.querySelector('.user-alert-modal-close').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        
        // ESC key
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                close();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    });
}

// Show error message
window.showError = function showError(message) {
    return showAlert(message, 'Ошибка', 'error');
};

// Show success message
window.showSuccess = function showSuccess(message) {
    return showAlert(message, 'Успешно', 'success');
};

// Load latest 3 news for dashboard
window.loadDashboardNews = async function loadDashboardNews() {
    const newsGrid = document.getElementById('dashboardNewsGrid');
    if (!newsGrid) return;
    
    try {
        const lang = localStorage.getItem('language') || 'ru';
        const response = await fetch(`${API_BASE_URL}/api/news/admin?per_page=100`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to load news');
        }
        
        const data = await response.json();
        
        // Фильтруем только активные и опубликованные новости
        const now = new Date();
        const activeNews = (data.items || []).filter(news => {
            if (!news.is_active) return false;
            
            const publishedAt = new Date(news.published_at);
            if (publishedAt > now) return false;
            
            if (news.expires_at) {
                const expiresAt = new Date(news.expires_at);
                if (expiresAt <= now) return false;
            }
            
            return true;
        });
        
        // Сортируем по приоритету и дате, берем первые 3
        const sortedNews = [...activeNews].sort((a, b) => {
            if (b.priority !== a.priority) {
                return b.priority - a.priority;
            }
            return new Date(b.published_at) - new Date(a.published_at);
        }).slice(0, 3);
        
        renderDashboardNews(sortedNews, lang);
    } catch (error) {
        console.error('Error loading dashboard news:', error);
        const newsGrid = document.getElementById('dashboardNewsGrid');
        if (newsGrid) {
            newsGrid.innerHTML = '<div class="text-center p-4 text-muted">Не удалось загрузить новости</div>';
        }
    }
};

function renderDashboardNews(newsItems, lang) {
    const newsGrid = document.getElementById('dashboardNewsGrid');
    if (!newsGrid) return;
    
    if (!newsItems || newsItems.length === 0) {
        newsGrid.innerHTML = '<div class="text-center p-4 text-muted" data-i18n="user_no_news">Нет новостей</div>';
        // Применяем переводы если доступны
        if (window.applyTranslations) {
            setTimeout(() => window.applyTranslations(), 100);
        }
        return;
    }
    
    const iconMap = {
        'info': 'bi-info-circle-fill',
        'announcement': 'bi-megaphone-fill',
        'star': 'bi-star-fill',
        'warning': 'bi-exclamation-triangle-fill',
        'calendar': 'bi-calendar-event-fill',
        'tools': 'bi-tools'
    };
    
    newsGrid.innerHTML = newsItems.map((news, index) => {
        // Парсим JSON поля если нужно
        let title, content;
        try {
            title = typeof news.title === 'string' ? JSON.parse(news.title) : news.title;
            content = typeof news.content === 'string' ? JSON.parse(news.content) : news.content;
        } catch (e) {
            console.error('Error parsing news JSON:', e, news);
            title = { ru: 'Ошибка загрузки', az: 'Yükləmə xətası', en: 'Loading error' };
            content = { ru: 'Не удалось загрузить содержимое', az: 'Məzmun yüklənə bilmədi', en: 'Failed to load content' };
        }
        
        // Выбираем язык с правильным fallback
        const titleText = (title[lang] && title[lang].trim()) || 
                         (title.ru && title.ru.trim()) || 
                         (title.az && title.az.trim()) || 
                         (title.en && title.en.trim()) || 
                         'Без заголовка';
        const contentText = (content[lang] && content[lang].trim()) || 
                           (content.ru && content.ru.trim()) || 
                           (content.az && content.az.trim()) || 
                           (content.en && content.en.trim()) || 
                           'Нет содержания';
        
        // Форматируем дату
        const locale = lang === 'ru' ? 'ru-RU' : (lang === 'az' ? 'az' : 'en-US');
        let publishedDate;
        try {
            publishedDate = new Date(news.published_at).toLocaleDateString(locale, {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
            if (publishedDate.includes('M')) {
                throw new Error('Fallback');
            }
        } catch (e) {
            const d = new Date(news.published_at);
            publishedDate = `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth() + 1).toString().padStart(2, '0')}.${d.getFullYear()}`;
        }
        
        // Экранируем HTML
        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        };
        
        const iconColor = news.icon_color || '#667eea';
        // Создаем тень с тем же цветом, но прозрачностью 0.4 для эффекта свечения
        const iconShadow = `0 4px 15px ${iconColor}66`;
        
        return `
            <div class="news-item" onclick="if(window.openNewsDetail){window.openNewsDetail(${news.id})}">
                <div class="news-icon" style="background-color: ${iconColor} !important; box-shadow: ${iconShadow} !important;">
                    <i class="bi ${iconMap[news.icon] || 'bi-info-circle-fill'}"></i>
                </div>
                <div class="news-content">
                    <h4>${escapeHtml(titleText)}</h4>
                    <p>${escapeHtml(contentText)}</p>
                    <span class="news-date"><i class="bi bi-calendar"></i> ${publishedDate}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Перерисовка новостей при смене языка
function refreshDashboardNews() {
    if (window.loadDashboardNews) {
        window.loadDashboardNews();
    }
}

// Слушаем смену языка
window.addEventListener('languageChanged', () => {
    refreshDashboardNews();
});

// Также слушаем изменения в localStorage для языка
window.addEventListener('storage', (e) => {
    if (e.key === 'language') {
        refreshDashboardNews();
    }
});

// Отслеживаем изменения языка через polling
let currentLang = localStorage.getItem('language') || 'ru';
const langCheckInterval = setInterval(() => {
    const newLang = localStorage.getItem('language') || 'ru';
    if (newLang !== currentLang) {
        currentLang = newLang;
        refreshDashboardNews();
    }
}, 300);

// Очищаем интервал при размонтировании
window.addEventListener('beforeunload', () => {
    if (langCheckInterval) clearInterval(langCheckInterval);
});

// ====== Notifications System ======
(function() {
    'use strict';
    
    const API_BASE = window.API_BASE_URL || 'http://localhost:8000';
    const notificationBtn = document.querySelector('.notification-btn');
    const notificationBadge = document.querySelector('.notification-badge');
    const notificationsModal = document.getElementById('notificationsModal');
    const notificationsClose = document.getElementById('notificationsClose');
    const notificationsList = document.getElementById('notificationsList');
    
    let notifications = [];
    
    // Format time
    function formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'только что';
        if (minutes < 60) return `${minutes} мин назад`;
        if (hours < 24) return `${hours} ч назад`;
        if (days < 7) return `${days} дн назад`;
        return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }
    
    // Load notifications
    async function loadNotifications() {
        try {
            const response = await fetch(`${API_BASE}/api/notifications/user/me?per_page=50`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            notifications = data.notifications || [];
            renderNotifications();
            updateNotificationCount();
        } catch (error) {
            console.error('Error loading notifications:', error);
            if (notificationsList) {
                notificationsList.innerHTML = '<div class="text-center p-4 text-muted">Не удалось загрузить уведомления</div>';
            }
        }
    }
    
    // Get unread count
    async function getUnreadCount() {
        try {
            const response = await fetch(`${API_BASE}/api/notifications/user/me/unread-count`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                return 0;
            }
            
            const data = await response.json();
            return data.count || 0;
        } catch (error) {
            console.error('Error fetching unread count:', error);
            return notifications.filter(n => n.status === 'UNREAD').length;
        }
    }
    
    // Update notification badge
    async function updateNotificationCount() {
        const count = await getUnreadCount();
        if (notificationBadge) {
            notificationBadge.textContent = count;
            notificationBadge.style.display = count > 0 ? 'flex' : 'none';
        }
    }
    
    // Render notifications
    function renderNotifications() {
        if (!notificationsList) return;
        
        if (notifications.length === 0) {
            notificationsList.innerHTML = '<div class="text-center p-4 text-muted">Нет уведомлений</div>';
            return;
        }
        
        const items = notifications.map(notif => {
            const isUnread = notif.status === 'UNREAD';
            const icon = notif.notification_type === 'INVOICE' 
                ? '<i class="bi bi-receipt"></i>' 
                : notif.notification_type === 'NEWS'
                ? '<i class="bi bi-bell"></i>'
                : '<i class="bi bi-bell"></i>';
            const iconColor = notif.notification_type === 'INVOICE' ? '#f59e0b' : '#667eea';
            
            return `
                <div class="notification-item" 
                     data-id="${notif.id}" 
                     data-type="${notif.notification_type || ''}"
                     data-related-id="${notif.related_id || ''}"
                     style="display:flex; gap:12px; align-items:flex-start; padding:12px 14px; border:1px solid rgba(255,255,255,0.08); border-radius:12px; margin-bottom:10px; background:${isUnread ? 'rgba(102,126,234,0.08)' : 'transparent'}; cursor:pointer; transition:background 0.2s;"
                     onmouseover="this.style.background='rgba(102,126,234,0.15)'" 
                     onmouseout="this.style.background='${isUnread ? 'rgba(102,126,234,0.08)' : 'transparent'}'">
                    <div style="width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#fff; background:${iconColor}; box-shadow:0 6px 16px rgba(0,0,0,.15); flex-shrink:0;">
                        ${icon}
                    </div>
                    <div style="flex:1; min-width:0;">
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                            <strong style="color:var(--text-primary); font-size:0.95rem;">${escapeHtml(notif.message)}</strong>
                            ${isUnread ? '<span class="badge" style="background:#10b981; height:20px; display:flex; align-items:center; padding:0 6px; font-size:0.7rem; flex-shrink:0;">НОВАЯ</span>' : ''}
                        </div>
                        <span style="font-size:0.8rem; color:var(--text-secondary);">${formatTime(notif.created_at)}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        notificationsList.innerHTML = items;
        
        // Add click handlers
        notificationsList.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', async function() {
                const notificationId = this.dataset.id;
                const notificationType = this.dataset.type;
                const relatedId = this.dataset.relatedId;
                
                // Mark as read
                try {
                    await fetch(`${API_BASE}/api/notifications/${notificationId}`, {
                        method: 'GET',
                        credentials: 'include'
                    });
                } catch (e) {
                    console.error('Error marking notification as read:', e);
                }
                
                // Close modal
                closeNotifications();
                
                // Navigate based on type
                if (notificationType === 'INVOICE' && relatedId) {
                    // Navigate to bills page and store invoice ID for filtering
                    try {
                        sessionStorage.setItem('billsFilterInvoiceIds', JSON.stringify([parseInt(relatedId)]));
                        sessionStorage.setItem('billsFilterStatuses', JSON.stringify(['ISSUED', 'PARTIAL', 'DRAFT', 'PAID']));
                    } catch (e) {
                        console.warn('Failed to store invoice filter in sessionStorage', e);
                    }
                    if (window.userSpaRouter) {
                        window.userSpaRouter.navigate('bills', true);
                    } else {
                        window.location.hash = 'bills';
                    }
                } else if (notificationType === 'NEWS' && relatedId) {
                    // Navigate to news page - store news ID for auto-opening modal
                    try {
                        sessionStorage.setItem('autoOpenNewsId', relatedId.toString());
                    } catch (e) {
                        console.warn('Failed to store news ID in sessionStorage', e);
                    }
                    if (window.userSpaRouter) {
                        window.userSpaRouter.navigate('news', true);
                    } else {
                        window.location.hash = 'news';
                    }
                    // Auto-open news modal after navigation (if function exists)
                    setTimeout(() => {
                        if (window.openNewsDetail && typeof window.openNewsDetail === 'function') {
                            window.openNewsDetail(parseInt(relatedId));
                        }
                    }, 1000);
                }
                
                // Reload notifications
                setTimeout(() => {
                    loadNotifications();
                }, 500);
            });
        });
    }
    
    // Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Open notifications modal
    function openNotifications() {
        if (!notificationsModal) return;
        notificationsModal.classList.add('show');
        document.body.style.overflow = 'hidden';
        loadNotifications();
    }
    
    // Close notifications modal
    function closeNotifications() {
        if (!notificationsModal) return;
        notificationsModal.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    // Event listeners
    if (notificationBtn) {
        notificationBtn.addEventListener('click', openNotifications);
    }
    
    if (notificationsClose) {
        notificationsClose.addEventListener('click', closeNotifications);
    }
    
    if (notificationsModal) {
        notificationsModal.addEventListener('click', function(e) {
            if (e.target === notificationsModal) {
                closeNotifications();
            }
        });
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && notificationsModal && notificationsModal.classList.contains('show')) {
            closeNotifications();
        }
    });
    
    // Load notifications count on page load
    updateNotificationCount();
    
    // Refresh count every 30 seconds
    setInterval(updateNotificationCount, 30000);
    
    // Expose functions globally
    window.loadUserNotifications = loadNotifications;
    window.updateUserNotificationCount = updateNotificationCount;
})();

console.log('📱 User dashboard loaded!');
