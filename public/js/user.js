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
        // Fallback to localStorage check for compatibility
        const authToken = localStorage.getItem('authToken');
        const userRole = localStorage.getItem('userRole');

        if (!authToken || userRole !== 'RESIDENT') {
            window.location.href = '/resident/login';
            return;
        }

        // Set user info from localStorage
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
const API_BASE_URL = 'http://localhost:8000';

// Store dashboard data globally
window.dashboardData = null;

// Load dashboard data from backend
window.loadDashboardData = async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/resident/dashboard`, {
            method: 'GET',
            credentials: 'include', // Include cookies for session auth
            headers: {
                'Content-Type': 'application/json',
            }
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
    // Update user info
    if (data.user) {
        const fullName = data.user.full_name || data.user.username || 'Пользователь';
        const userNameEl = document.querySelector('.user-name');
        const userAvatarEl = document.querySelector('.user-avatar');
        const greetingEl = document.querySelector('.resident-greeting');
        
        if (userNameEl) {
            userNameEl.textContent = fullName;
        }
        
        if (userAvatarEl) {
            const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            userAvatarEl.textContent = initials || fullName.substring(0, 2).toUpperCase();
        }

        if (greetingEl) {
            greetingEl.innerHTML = `<span data-i18n="user_greeting_prefix">Здравствуйте,</span> ${fullName}`;
        }
    }

    // Update summary (first resident or aggregate)
    if (data.residents && data.residents.length > 0) {
        const firstResident = data.residents[0];
        const summary = data.summary;

        // Update resident card
        const residentTag = document.querySelector('.resident-tag');
        if (residentTag && firstResident) {
            residentTag.textContent = firstResident.code;
        }
        
        // Set resident ID on "Подробнее" button
        const detailsBtn = document.querySelector('[data-user-route-target="resident"]');
        if (detailsBtn && firstResident) {
            detailsBtn.setAttribute('data-resident-id', firstResident.id.toString());
        }

        // Update month due
        const monthDueEl = document.querySelector('.resident-amount-box strong');
        if (monthDueEl) {
            monthDueEl.textContent = formatCurrency(summary.total_month);
        }

        // Update progress bar
        const progressBar = document.querySelector('.resident-progress-bar');
        const progressFill = document.querySelector('.resident-progress-fill');
        if (progressBar && progressFill && firstResident) {
            const percentage = firstResident.month_total > 0 
                ? (firstResident.month_paid / firstResident.month_total) * 100 
                : 0;
            progressFill.style.width = `${Math.min(percentage, 100)}%`;

            // Показываем короткий формат "оплачено/за месяц", например 0/112, по центру полосы
            const paidShort = Math.round(firstResident.month_paid || 0);
            const totalShort = Math.round(firstResident.month_total || 0);
            let progressTextSpan = progressBar.querySelector('.resident-progress-text');
            if (!progressTextSpan) {
                progressTextSpan = document.createElement('span');
                progressTextSpan.className = 'resident-progress-text';
                progressBar.appendChild(progressTextSpan);
            }
            progressTextSpan.textContent = `${paidShort}/${totalShort}`;
        }

        // Update detailed stats in resident card (use first resident's data)
        updateStatValue('.resident-stats-row > div:nth-child(1) .resident-stat-value', firstResident.debt_total);
        updateStatValue('.resident-stats-row > div:nth-child(2) .resident-stat-value', firstResident.advance_total, true);
        updateStatValue('.resident-stats-row > div:nth-child(3) .resident-stat-value', firstResident.pay_now);

        // Update summary cards (use aggregate summary)
        updateStatValue('.resident-summary-card:first-child .summary-value', summary.total_debt);
        updateStatValue('.resident-summary-card.accent .summary-value', summary.total_advance);
        
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
function updateStatValue(selector, value, isPositive = false) {
    const element = document.querySelector(selector);
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

        // "Погасить из аванса" (Pay from advance)
        const payFromAdvanceBtn = e.target.closest('[data-action="pay-from-advance"]');
        if (payFromAdvanceBtn && window.dashboardData && window.dashboardData.residents.length > 0) {
            e.preventDefault();
            const residentId = window.dashboardData.residents[0].id; // Use first resident for now
            await applyAdvance(residentId);
            return;
        }

        // "Оплатить за месяц" — оплачиваем только текущий месяц
        const payMonthBtn = e.target.closest('[data-action="pay-month"]');
        if (payMonthBtn && window.dashboardData) {
            e.preventDefault();
            const amount = summary.total_month || 0;
            startPaymentFlow('month', amount, summary);
            return;
        }

        // "Оплатить всё" — полное погашение долга по всем счетам
        const payAllBtn = e.target.closest('[data-action="pay-all"]');
        if (payAllBtn && window.dashboardData) {
            e.preventDefault();
            const amount = summary.total_debt || 0;
            startPaymentFlow('all', amount, summary);
            return;
        }
    });
}

// Запуск цепочки оплаты: сохраняем параметры и переходим на страницу оплаты
function startPaymentFlow(scope, amount, summaryFromDashboard) {
    // Код резидента для отображения на странице оплаты
    const residentTagEl = document.querySelector('.resident-tag');
    const residentCode = residentTagEl ? residentTagEl.textContent.trim() : '';

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
        if (summaryFromDashboard && typeof summaryFromDashboard === 'object') {
            sessionStorage.setItem('paymentSummary', JSON.stringify(summaryFromDashboard));
        }
        if (residentCode) {
            sessionStorage.setItem('paymentResidentCode', residentCode);
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
async function applyAdvance(residentId) {
    if (!confirm('Применить аванс к открытым счетам?')) {
        return;
    }

    try {
        const formData = new FormData();
        formData.append('resident_id', residentId);

        const response = await fetch(`${API_BASE_URL}/resident/apply-advance`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Reload dashboard data
        await loadDashboardData();
        
        if (window.showSuccess) {
            showSuccess('Аванс успешно применён к счетам!');
        } else {
            alert('Аванс успешно применён к счетам!');
        }
    } catch (error) {
        console.error('Error applying advance:', error);
        if (window.showError) {
            showError('Не удалось применить аванс. Попробуйте позже.');
        } else {
            alert('Не удалось применить аванс. Попробуйте позже.');
        }
    }
}

// Show error message
function showError(message) {
    // You can implement a toast notification here
    console.error(message);
    // For now, just log it
}

// Show success message
function showSuccess(message) {
    console.log(message);
    // You can implement a toast notification here
}

console.log('📱 User dashboard loaded!');
