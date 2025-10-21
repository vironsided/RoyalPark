// Accountant Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initSidebarToggle();
    initNavigation();
    initChart();
    addCardAnimations();
    addRippleEffect();
    initFilters();
    initReportGeneration();
});

function checkAuth() {
    const authToken = localStorage.getItem('authToken');
    const userRole = localStorage.getItem('userRole');

    if (!authToken || userRole !== 'accountant') {
        window.location.href = '/login.html';
        return;
    }

    const username = localStorage.getItem('username') || 'Бухгалтер';
    const userNameEl = document.querySelector('.user-name');
    const userAvatarEl = document.querySelector('.user-avatar');
    
    if (userNameEl) userNameEl.textContent = username;
    if (userAvatarEl) userAvatarEl.textContent = username.substring(0, 2).toUpperCase();
}

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

function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
                e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function initChart() {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(17, 153, 142, 0.8)');
    gradient.addColorStop(1, 'rgba(56, 239, 125, 0.1)');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт'],
            datasets: [{
                label: 'Платежи (₼)',
                data: [180000, 220000, 195000, 250000, 240000, 270000, 280000, 260000, 290000, 240000],
                backgroundColor: gradient,
                borderColor: 'rgba(17, 153, 142, 1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#fff',
                pointBorderColor: 'rgba(17, 153, 142, 1)',
                pointBorderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: (context) => '₼' + context.parsed.y.toLocaleString()
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: {
                        callback: (value) => '₼' + value.toLocaleString()
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function addCardAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.stat-card, .card').forEach(card => {
        observer.observe(card);
    });
}

function addRippleEffect() {
    document.querySelectorAll('.nav-item, button').forEach(el => {
        el.addEventListener('click', function(e) {
            if (this.classList.contains('logout-btn')) return;
            
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                transform: scale(0);
                animation: ripple-anim 0.6s ease-out;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

document.addEventListener('click', (e) => {
    if (e.target.closest('.logout-btn')) {
        localStorage.clear();
        window.location.href = '/login.html';
    }
});

const style = document.createElement('style');
style.textContent = '@keyframes ripple-anim { to { transform: scale(2); opacity: 0; } }';
document.head.appendChild(style);

// 💰 FILTERS FUNCTIONALITY
function initFilters() {
    const applyBtn = document.getElementById('applyFilters');
    const resetBtn = document.getElementById('resetFilters');
    const exportExcelBtn = document.querySelector('.btn-export.excel');
    const exportPdfBtn = document.querySelector('.btn-export.pdf');
    
    if (applyBtn) {
        applyBtn.addEventListener('click', applyFilters);
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', resetFilters);
    }
    
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', () => exportTable('excel'));
    }
    
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', () => exportTable('pdf'));
    }
}

function applyFilters() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const status = document.getElementById('statusFilter').value;
    const method = document.getElementById('methodFilter').value;
    const building = document.getElementById('buildingFilter').value;
    
    console.log('Applying filters:', { dateFrom, dateTo, status, method, building });
    
    // Анимация кнопки
    const btn = document.getElementById('applyFilters');
    btn.style.transform = 'scale(0.95)';
    setTimeout(() => {
        btn.style.transform = 'scale(1)';
    }, 100);
    
    // Показать уведомление
    showNotification('success', 'Фильтры применены успешно!');
    
    // TODO: В реальном приложении здесь будет запрос к API
    filterTable({ dateFrom, dateTo, status, method, building });
}

function resetFilters() {
    document.getElementById('dateFrom').value = '2024-10-01';
    document.getElementById('dateTo').value = '2024-10-17';
    document.getElementById('statusFilter').value = 'all';
    document.getElementById('methodFilter').value = 'all';
    document.getElementById('buildingFilter').value = 'all';
    
    showNotification('info', 'Фильтры сброшены');
    
    // Сбросить фильтрацию таблицы
    filterTable(null);
}

function filterTable(filters) {
    const table = document.getElementById('paymentsTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    if (!filters) {
        // Показать все строки
        rows.forEach(row => row.style.display = '');
        return;
    }
    
    // Фильтрация (упрощенная для демо)
    rows.forEach(row => {
        let show = true;
        
        // Фильтр по статусу
        if (filters.status && filters.status !== 'all') {
            const badge = row.querySelector('.badge');
            if (badge) {
                const status = badge.textContent.trim();
                if (filters.status === 'paid' && !status.includes('Оплачено')) show = false;
                if (filters.status === 'pending' && !status.includes('обработке')) show = false;
            }
        }
        
        // Фильтр по методу
        if (filters.method && filters.method !== 'all') {
            const methodBadge = row.querySelector('.payment-method');
            if (methodBadge && !methodBadge.classList.contains(filters.method)) {
                show = false;
            }
        }
        
        row.style.display = show ? '' : 'none';
        
        // Добавить анимацию
        if (show) {
            row.style.animation = 'fadeInUp 0.3s ease-out';
        }
    });
}

function exportTable(format) {
    const formatNames = { excel: 'Excel', pdf: 'PDF' };
    showNotification('success', `Экспорт в ${formatNames[format]} начат...`);
    
    // TODO: Реальный экспорт
    setTimeout(() => {
        showNotification('success', `Файл ${formatNames[format]} готов к скачиванию!`);
    }, 1500);
}

// 📊 REPORT GENERATION FUNCTIONALITY
function initReportGeneration() {
    const generateBtns = document.querySelectorAll('.btn-generate');
    const batchBtn = document.querySelector('.btn-batch-generate');
    
    generateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const reportType = this.getAttribute('data-report');
            const card = this.closest('.report-card');
            const period = card ? card.querySelector('.report-period').value : 'Текущий месяц';
            
            generateReport(reportType, period, this);
        });
    });

    if (batchBtn) {
        batchBtn.addEventListener('click', generateAllReports);
    }
}

function generateReport(type, period, button) {
    const reportNames = {
        financial: 'Финансовый отчет',
        payments: 'Отчет по платежам',
        debts: 'Отчет по задолженностям',
        analytics: 'Аналитический отчет',
        buildings: 'Отчет по зданиям',
        tax: 'Налоговый отчет'
    };
    
    const reportName = reportNames[type] || 'Отчет';
    
    // Анимация кнопки
    button.disabled = true;
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Генерация...';
    button.style.opacity = '0.7';
    
    // Симуляция генерации
    setTimeout(() => {
        button.disabled = false;
        button.innerHTML = originalHTML;
        button.style.opacity = '1';
        
        // Показать успешное уведомление
        showNotification('success', `${reportName} (${period}) успешно сформирован!`);
        
        // Анимация карточки
        const card = button.closest('.report-card');
        if (card) {
            card.style.animation = 'none';
            setTimeout(() => {
                card.style.animation = 'pulse 0.5s ease';
            }, 10);
        }
        
        // Обновить счетчик отчетов
        updateReportCounter();
        
        // TODO: Реальная генерация отчета и скачивание
    }, 2000);
}

function generateAllReports() {
    const btn = document.querySelector('.btn-batch-generate');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Генерация всех отчетов...';
    btn.style.opacity = '0.7';
    
    showNotification('info', 'Генерация всех отчетов начата...');
    
    // Симуляция
    setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-collection"></i> Сформировать все отчеты';
        btn.style.opacity = '1';
        
        showNotification('success', '6 отчетов успешно сформированы!');
        updateReportCounter();
    }, 4000);
}

function updateReportCounter() {
    const counterEl = document.querySelector('.quick-stat-item:first-child .stat-value');
    if (counterEl) {
        const current = parseInt(counterEl.textContent);
        counterEl.textContent = current + 1;
        
        // Анимация
        counterEl.style.animation = 'none';
        setTimeout(() => {
            counterEl.style.animation = 'pulse 0.5s ease';
        }, 10);
    }
}

// Универсальная функция уведомлений
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        background: ${type === 'success' ? 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' : 
                      type === 'error' ? 'linear-gradient(135deg, #f5576c 0%, #f093fb 100%)' : 
                      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'};
        color: white;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        animation: slideInRight 0.5s ease-out;
        z-index: 10000;
    `;
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.5s ease-out';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Добавить стили для уведомлений
const notificationStyle = document.createElement('style');
notificationStyle.textContent = `
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
`;
document.head.appendChild(notificationStyle);

console.log('💰 Accountant dashboard loaded!');
