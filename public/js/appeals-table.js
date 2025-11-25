// Appeals table variant: compact list of resident complaints
(function() {
    'use strict';

    const statusStyles = {
        read: { text: 'прочитано', className: 'bg-success' },
        unread: { text: 'не прочитано', className: 'bg-warning text-dark' },
        in_progress: { text: 'в процессе', className: 'bg-primary' },
        escalated: { text: 'на доп. проверке', className: 'bg-danger' }
    };

    const state = {
        appeals: []
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }

    function init() {
        const users = (TestData?.users || []).reduce((acc, user) => {
            acc[user.id] = user;
            return acc;
        }, {});

        state.appeals = (TestData?.debts || []).map((entry) => {
            const resident = users[entry.userId] || {};
            const submitted = entry.submittedAt || `${entry.dueDate || '2024-01-01'}T09:00:00`;
            const [block, apt] = splitApartment(entry.apartment);
            return {
                id: entry.id,
                createdAt: submitted,
                block: block || resident.building || '—',
                home: apt || resident.apartment || '—',
                resident: resident.name || entry.userName || '—',
                phone: resident.phone || '—',
                email: resident.email || '—',
                status: deriveStatus(entry),
                raw: entry,
                residentData: resident
            };
        });

        cacheDom();
        applyFilters();
        bindEvents();
    }

    let tableBody, emptyState, statusSelect, searchInput, modalOverlay;
    let modalResident, modalApartment, modalContacts, modalDescription;

    function cacheDom() {
        tableBody = document.getElementById('appealsTableBody');
        emptyState = document.getElementById('appealsEmptyState');
        statusSelect = null;
        searchInput = null;
        modalOverlay = document.getElementById('appealModal');
        modalResident = document.getElementById('modalResident');
        modalApartment = document.getElementById('modalApartment');
        modalContacts = document.getElementById('modalContacts');
        modalDescription = document.getElementById('modalDescription');
    }

    function bindEvents() {
        statusSelect?.addEventListener('change', applyFilters);
        searchInput?.addEventListener('input', debounce(applyFilters, 200));
        document.getElementById('appealsRefreshBtn')?.addEventListener('click', applyFilters);

        tableBody?.addEventListener('click', (event) => {
            const viewBtn = event.target.closest('[data-action="view"]');
            const deleteBtn = event.target.closest('[data-action="delete"]');
            if (viewBtn) {
                const appeal = findAppeal(viewBtn.dataset.id);
                if (appeal) openModal(appeal);
            } else if (deleteBtn) {
                const appeal = findAppeal(deleteBtn.dataset.id);
                if (appeal) deleteAppeal(appeal.id);
            }
        });

        document.getElementById('appealModalClose')?.addEventListener('click', closeModal);
        document.getElementById('appealModalDismiss')?.addEventListener('click', closeModal);
        modalOverlay?.addEventListener('click', (event) => {
            if (event.target === modalOverlay) closeModal();
        });
    }

    function applyFilters() {
        renderTable();
    }

    function renderTable() {
        if (!tableBody) return;
        if (!state.appeals.length) {
            tableBody.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        tableBody.innerHTML = state.appeals.map(appeal => {
            const status = statusStyles[appeal.status] || statusStyles.unread;
            return `
                <tr>
                    <td>${formatDateTime(appeal.createdAt)}</td>
                    <td>${appeal.block}</td>
                    <td>${appeal.home}</td>
                    <td>${appeal.resident}</td>
                    <td>${appeal.phone}</td>
                    <td>${appeal.email}</td>
                    <td>
                        <span class="appeals-status-badge ${status.className}">${status.text}</span>
                    </td>
                    <td class="text-end">
                        <button class="btn btn-outline-primary btn-sm" data-action="view" data-id="${appeal.id}">
                            Просмотр
                        </button>
                        <button class="btn btn-outline-danger btn-sm ms-2" data-action="delete" data-id="${appeal.id}">
                            Удалить
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function openModal(appeal) {
        modalApartment.textContent = `${appeal.block} / ${appeal.home}`;
        modalResident.textContent = appeal.resident;
        modalContacts.textContent = `${appeal.phone} / ${appeal.email}`;
        modalDescription.textContent = appeal.raw?.residentComment || appeal.raw?.complaintReason || '—';

        appeal.status = 'read';
        appeal.raw.viewed = true;
        modalOverlay?.classList.add('show');
        applyFilters();
    }

    function closeModal() {
        modalOverlay?.classList.remove('show');
    }

    function deleteAppeal(id) {
        const index = state.appeals.findIndex(a => String(a.id) === String(id));
        if (index >= 0) {
            state.appeals.splice(index, 1);
            applyFilters();
        }
    }

    function findAppeal(id) {
        return state.appeals.find(a => String(a.id) === String(id));
    }

    function deriveStatus(entry) {
        if (!entry.viewed) return 'unread';
        if (entry.stage === 'in_progress') return 'in_progress';
        if (entry.stage === 'escalated') return 'escalated';
        return 'read';
    }

    function splitApartment(apartment = '') {
        if (!apartment) return ['—', '—'];
        const parts = apartment.split('-');
        return [parts[0] || '—', parts[1] || '—'];
    }

    function formatDateTime(value) {
        if (!value) return '—';
        const date = new Date(value);
        return date.toLocaleString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function debounce(fn, delay = 200) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn.apply(null, args), delay);
        };
    }

})();

