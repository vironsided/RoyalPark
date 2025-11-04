// 💰 Debts Management Page - RoyalPark Admin Panel

(function() {
    'use strict';

    let debts = [];

    // Initialize page
    function init() {
        loadDebts();
        updateStats();
    }

    // Load debts from test data
    function loadDebts() {
        debts = TestData.debts;
        renderDebts();
    }

    // Render debts
    function renderDebts() {
        const container = document.getElementById('debtsList');
        if (!container) return;

        container.innerHTML = debts.map((debt, index) => `
            <div class="card debt-card ${debt.status} mb-4 animate__animated animate__fadeInUp" style="animation-delay: ${index * 0.1}s">
                <div class="card-body">
                    <div class="row">
                        <!-- Left Column: User Info -->
                        <div class="col-lg-4 border-end">
                            <div class="d-flex align-items-center mb-3">
                                <div class="user-avatar-sm me-3" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 50%; color: white; font-weight: bold; font-size: 1.25rem;">
                                    ${getInitials(debt.userName)}
                                </div>
                                <div>
                                    <h5 class="mb-1">${debt.userName}</h5>
                                    <p class="mb-0 text-muted">
                                        <i class="bi bi-house-door"></i> ${debt.apartment}
                                    </p>
                                </div>
                            </div>

                            <div class="mb-3">
                                <span class="badge ${debt.status === 'critical' ? 'bg-danger' : 'bg-warning'} mb-2">
                                    <i class="bi bi-exclamation-triangle-fill"></i> 
                                    ${debt.status === 'critical' ? 'КРИТИЧЕСКАЯ' : 'ПРОСРОЧЕНА'}
                                </span>
                                <span class="overdue-days ms-2">
                                    <i class="bi bi-calendar-x"></i> ${debt.daysOverdue} дней
                                </span>
                            </div>

                            <div class="alert alert-danger mb-3">
                                <h4 class="mb-0">${debt.amount.toFixed(2)} ₼</h4>
                                <small>Сумма задолженности</small>
                            </div>

                            <div class="mb-2">
                                <small class="text-muted">Период:</small><br>
                                <strong>${debt.period}</strong>
                            </div>
                            <div class="mb-2">
                                <small class="text-muted">Срок оплаты:</small><br>
                                <strong class="text-danger">${formatDate(debt.dueDate)}</strong>
                            </div>
                        </div>

                        <!-- Middle Column: Tasks -->
                        <div class="col-lg-4 border-end">
                            <h6 class="mb-3">
                                <i class="bi bi-person-badge"></i> Ответственный
                            </h6>
                            <div class="mb-3">
                                <div class="d-flex align-items-center">
                                    <div class="user-avatar-sm me-2" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%; color: white; font-weight: bold; font-size: 0.875rem;">
                                        ${getInitials(debt.assignedTo)}
                                    </div>
                                    <strong>${debt.assignedTo}</strong>
                                </div>
                            </div>

                            <h6 class="mb-3 mt-4">
                                <i class="bi bi-list-check"></i> Текущая задача
                            </h6>
                            <div class="task-badge">
                                <i class="bi bi-gear-fill"></i>
                                <span>${debt.task}</span>
                            </div>

                            <h6 class="mb-3 mt-4">
                                <i class="bi bi-chat-left-text"></i> Примечания
                            </h6>
                            <div class="alert alert-info mb-0">
                                <small>${debt.notes}</small>
                            </div>
                        </div>

                        <!-- Right Column: Timeline & Actions -->
                        <div class="col-lg-4">
                            <h6 class="mb-3">
                                <i class="bi bi-clock-history"></i> История действий
                            </h6>
                            <div class="timeline">
                                ${getDebtTimeline(debt)}
                            </div>

                            <div class="mt-4 d-grid gap-2">
                                <button class="btn btn-success" onclick="markAsPaid(${debt.id})">
                                    <i class="bi bi-check-circle"></i> Отметить как оплачено
                                </button>
                                <button class="btn btn-primary" onclick="contactUser(${debt.userId})">
                                    <i class="bi bi-telephone"></i> Связаться с жильцом
                                </button>
                                <button class="btn btn-warning" onclick="sendReminder(${debt.id})">
                                    <i class="bi bi-envelope"></i> Отправить напоминание
                                </button>
                                <button class="btn btn-outline-danger" onclick="legalAction(${debt.id})">
                                    <i class="bi bi-file-earmark-text"></i> Юридические меры
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Get initials from name
    function getInitials(name) {
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    // Generate timeline for debt
    function getDebtTimeline(debt) {
        const timeline = [
            {
                date: debt.dueDate,
                text: 'Срок оплаты истёк',
                icon: 'exclamation-circle-fill',
                color: 'danger'
            },
            {
                date: new Date().toISOString().split('T')[0],
                text: debt.task,
                icon: 'gear-fill',
                color: 'primary'
            }
        ];

        // Add status-specific events
        if (debt.status === 'critical') {
            timeline.push({
                date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                text: 'Юридическое уведомление',
                icon: 'file-earmark-text-fill',
                color: 'warning'
            });
        }

        return timeline.map((item, index) => `
            <div class="timeline-item">
                <div class="timeline-dot" style="background: var(--bs-${item.color});"></div>
                <div>
                    <small class="text-muted">${formatDate(item.date)}</small>
                    <p class="mb-0">
                        <i class="bi bi-${item.icon} text-${item.color}"></i>
                        ${item.text}
                    </p>
                </div>
            </div>
        `).join('');
    }

    // Update statistics
    function updateStats() {
        const totalDebts = debts.length;
        const overdueDebts = debts.filter(d => d.status === 'overdue' || d.status === 'critical').length;
        const totalAmount = debts.reduce((sum, d) => sum + d.amount, 0);
        const activeTasks = debts.filter(d => d.assignedTo).length;

        document.getElementById('totalDebts').textContent = totalDebts;
        document.getElementById('overdueDebts').textContent = overdueDebts;
        document.getElementById('totalAmount').textContent = totalAmount.toFixed(2) + '₼';
        document.getElementById('activeTasks').textContent = activeTasks;
    }

    // Utility: create or get a reusable modal container
    function getModalRoot() {
        let root = document.getElementById('debtsModalRoot');
        if (!root) {
            root = document.createElement('div');
            root.id = 'debtsModalRoot';
            document.body.appendChild(root);
        }
        return root;
    }

    // In-app confirm modal (returns Promise<boolean>)
    function showConfirmModal(options) {
        const {
            title = 'Подтвердите действие',
            message = '',
            confirmText = 'Подтвердить',
            cancelText = 'Отмена'
        } = options || {};

        return new Promise((resolve) => {
            const root = getModalRoot();
            const overlay = document.createElement('div');
            overlay.className = 'account-modal-overlay show';
            overlay.innerHTML = `
                <div class="account-modal" style="max-width:520px">
                    <div class="account-modal-header">
                        <h2>${title}</h2>
                        <button class="account-modal-close">&times;</button>
                    </div>
                    <div class="account-modal-body">
                        <div style="display:flex; gap:12px; align-items:flex-start;">
                            <div style="width:38px; height:38px; border-radius:10px; background:#f59e0b; color:#fff; display:flex; align-items:center; justify-content:center; box-shadow:0 8px 20px rgba(0,0,0,.2)">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                            </div>
                            <div style="white-space:pre-wrap;">${message}</div>
                        </div>
                    </div>
                    <div class="account-modal-footer">
                        <button class="account-btn account-btn-secondary btn-cancel">${cancelText}</button>
                        <button class="account-btn account-btn-primary btn-ok">${confirmText}</button>
                    </div>
                </div>`;

            function close(result) {
                overlay.classList.remove('show');
                setTimeout(() => overlay.remove(), 150);
                document.body.style.overflow = '';
                resolve(result);
            }

            overlay.addEventListener('click', (e) => { if (e.target === overlay) close(false); });
            overlay.querySelector('.account-modal-close').addEventListener('click', () => close(false));
            overlay.querySelector('.btn-cancel').addEventListener('click', () => close(false));
            overlay.querySelector('.btn-ok').addEventListener('click', () => close(true));
            document.addEventListener('keydown', function esc(e){ if(e.key==='Escape'){ close(false); document.removeEventListener('keydown', esc);} });

            root.appendChild(overlay);
            document.body.style.overflow = 'hidden';
        });
    }

    // In-app info modal
    function showInfoModal(options) {
        const { title = 'Информация', message = '', okText = 'OK' } = options || {};
        return new Promise((resolve) => {
            const root = getModalRoot();
            const overlay = document.createElement('div');
            overlay.className = 'account-modal-overlay show';
            overlay.innerHTML = `
                <div class="account-modal" style="max-width:520px">
                    <div class="account-modal-header">
                        <h2>${title}</h2>
                        <button class="account-modal-close">&times;</button>
                    </div>
                    <div class="account-modal-body">${message}</div>
                    <div class="account-modal-footer">
                        <button class="account-btn account-btn-primary btn-ok">${okText}</button>
                    </div>
                </div>`;
            function close() {
                overlay.classList.remove('show');
                setTimeout(() => overlay.remove(), 150);
                document.body.style.overflow = '';
                resolve();
            }
            overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
            overlay.querySelector('.account-modal-close').addEventListener('click', close);
            overlay.querySelector('.btn-ok').addEventListener('click', close);
            document.addEventListener('keydown', function esc(e){ if(e.key==='Escape'){ close(); document.removeEventListener('keydown', esc);} });
            root.appendChild(overlay);
            document.body.style.overflow = 'hidden';
        });
    }

    // Mark as paid
    window.markAsPaid = function(debtId) {
        const debt = debts.find(d => d.id === debtId);
        if (!debt) return;

        showConfirmModal({
            title: 'Подтверждение оплаты',
            message: `Подтвердить оплату ${debt.amount.toFixed(2)} ₼ от ${debt.userName}?`,
            confirmText: 'Подтвердить',
            cancelText: 'Отмена'
        }).then((ok) => {
            if (!ok) return;
            const index = debts.findIndex(d => d.id === debtId);
            debts.splice(index, 1);
            renderDebts();
            updateStats();
            showNotification(`Задолженность ${debt.userName} отмечена как оплаченная!`, 'success');
        });
    };

    // Contact user
    window.contactUser = function(userId) {
        const user = TestData.users.find(u => u.id === userId);
        if (!user) return;

        const message = `<div style="line-height:1.7">
            <div><strong>Звонок:</strong> ${user.phone}</div>
            <div><strong>Email:</strong> ${user.email}</div>
        </div>`;
        showInfoModal({ title: 'Контактные данные', message, okText: 'Понятно' })
            .then(() => showNotification(`Инициирован контакт с ${user.name}`, 'info'));
    };

    // Send reminder
    window.sendReminder = function(debtId) {
        const debt = debts.find(d => d.id === debtId);
        if (!debt) return;

        showNotification(`SMS-напоминание отправлено ${debt.userName}`, 'info');
    };

    // Legal action
    window.legalAction = function(debtId) {
        const debt = debts.find(d => d.id === debtId);
        if (!debt) return;

        showConfirmModal({
            title: 'Юридические меры',
            message: `Начать юридическую процедуру для ${debt.userName}?\nСумма: ${debt.amount.toFixed(2)} ₼`,
            confirmText: 'Начать',
            cancelText: 'Отмена'
        }).then((ok) => {
            if (!ok) return;
            debt.status = 'critical';
            debt.task = 'Юридическое уведомление отправлено';
            renderDebts();
            showNotification('Юридическая процедура инициирована', 'warning');
        });
    };

    // Format date
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Show notification
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3 animate__animated animate__fadeInRight`;
        notification.style.zIndex = '10000';
        notification.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}-fill me-2"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.remove('animate__fadeInRight');
            notification.classList.add('animate__fadeOutRight');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();












