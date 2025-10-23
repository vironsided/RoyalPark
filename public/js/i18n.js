// 🌍 Multi-language Support System
// Система поддержки нескольких языков

const translations = {
    // 🇷🇺 РУССКИЙ
    ru: {
        // Common
        search: "Поиск...",
        search_payments: "Поиск платежей...",
        logout: "Выход",
        settings: "Настройки",
        home: "Главная",
        save: "Сохранить",
        cancel: "Отмена",
        apply: "Применить",
        reset: "Сбросить",
        show_menu: "Показать меню",
        
        // Login Page
        login_title: "Добро пожаловать в RoyalPark",
        login_subtitle: "Система управления коммунальными услугами",
        login_select_role: "Выберите роль",
        username: "Имя пользователя",
        username_placeholder: "Введите имя пользователя",
        password: "Пароль",
        password_placeholder: "Введите пароль",
        login_button: "Войти в систему",
        remember_me: "Запомнить меня",
        forgot_password: "Забыли пароль?",
        secure_connection: "Защищенное соединение",
        copyright: "© 2024 RoyalPark. Все права защищены.",
        
        // Roles
        role_admin: "Администратор",
        role_user: "Жилец",
        role_maintenance: "Служба",
        role_accountant: "Бухгалтер",
        system_admin: "Системный админ",
        
        // Navigation Sections
        nav_main: "ГЛАВНОЕ",
        nav_management: "УПРАВЛЕНИЕ",
        nav_finance: "ФИНАНСЫ",
        nav_maintenance: "ОБСЛУЖИВАНИЕ",
        
        // Navigation
        nav_dashboard: "Панель управления",
        nav_payments: "Платежи",
        nav_accounts: "Счета",
        nav_debts: "Задолженности",
        nav_reports: "Отчеты",
        nav_financial: "Финансовые",
        nav_analytics: "Аналитика",
        nav_documents: "Документы",
        nav_system: "СИСТЕМА",
        nav_requests: "Заявки",
        nav_repair_requests: "Заявки на ремонт",
        nav_meters: "Счетчики",
        nav_news: "Новости",
        nav_profile: "Профиль",
        nav_users: "Пользователи",
        nav_buildings: "Здания",
        nav_apartments: "Квартиры",
        nav_blocks: "Блоки",
        nav_tariffs: "Тарифы",
        nav_residents: "Резиденты",
        nav_tenants: "Жители",
        nav_readings: "Показатели",
        nav_checks: "Проверки",
        nav_personnel: "Персонал",
        
        // Dashboard
        dashboard_title: "Панель управления",
        dashboard_admin: "Панель администратора",
        dashboard_user: "Панель жильца",
        dashboard_maintenance: "Панель службы",
        dashboard_accountant: "Панель бухгалтера",
        
        // Stats Cards
        income_month: "Доход за месяц",
        payments_today: "Платежей сегодня",
        payments_month: "Платежи за месяц",
        debts: "Задолженности",
        payability: "Оплачиваемость",
        processed: "Обработано",
        requires_attention: "Требует внимания",
        excellent_indicator: "Отличный показатель",
        total_users: "Всего пользователей",
        buildings: "Зданий",
        active_requests: "Активные заявки",
        per_month: "за месяц",
        per_week: "за неделю",
        new: "новых",
        
        // Time periods
        week: "Неделя",
        month: "Месяц",
        year: "Год",
        today: "Сегодня",
        yesterday: "Вчера",
        
        // Days of week
        monday: "Пн",
        tuesday: "Вт",
        wednesday: "Ср",
        thursday: "Чт",
        friday: "Пт",
        saturday: "Сб",
        sunday: "Вс",
        
        // Activity
        latest_activity: "Последняя активность",
        latest_payments: "Последние платежи",
        new_payment_received: "Новый платеж получен",
        new_repair_request: "Новая заявка на ремонт",
        meter_reading: "Показания счетчика",
        check_completed: "Проверка завершена",
        new_user: "Новый пользователь",
        debt_reminder: "Напоминание о задолженности",
        apartment: "Квартира",
        building: "Здание",
        minutes_ago: "минут назад",
        hour_ago: "час назад",
        hours_ago: "часа назад",
        apartments: "квартир",
        
        // Payment Statistics
        payment_statistics: "Статистика платежей",
        payment_dynamics: "Динамика платежей",
        
        // Table Headers
        id: "ID",
        user: "Пользователь",
        payer: "Плательщик",
        amount: "Сумма",
        date: "Дата",
        status: "Статус",
        status_paid: "Оплачено",
        status_processing: "В обработке",
        status_pending: "В обработке",
        status_failed: "Отклонено",
        
        // Filters
        filters_title: "Фильтры платежей",
        filter_period: "Период",
        filter_status: "Статус",
        filter_method: "Метод оплаты",
        filter_building: "Здание",
        all_statuses: "Все статусы",
        all_methods: "Все методы",
        all_buildings: "Все здания",
        status_paid: "Оплачено",
        status_pending: "В обработке",
        status_failed: "Отклонено",
        
        // Reports
        reports_title: "Генерация отчетов",
        report_financial: "Финансовый отчет",
        report_payments: "Отчет по платежам",
        report_debts: "Отчет по задолженностям",
        report_analytics: "Аналитический отчет",
        report_buildings: "Отчет по зданиям",
        report_tax: "Налоговый отчет",
        generate: "Сформировать",
        generate_all: "Сформировать все отчеты",
        
        // Meters
        meters_title: "Проверка счетчиков",
        meter_electricity: "Электричество",
        meter_cold_water: "Холодная вода",
        meter_hot_water: "Горячая вода",
        meter_previous: "Предыдущее",
        meter_current: "Текущее",
        meter_consumption: "Потребление",
        meter_approve: "Утвердить",
        meter_reject: "Отклонить",
        meter_investigate: "Расследовать",
        status_pending_check: "На проверке",
        status_verified: "Проверено",
        status_anomaly: "Аномалия",
        
        // Notifications
        theme_light: "Светлая тема",
        theme_dark: "Темная тема",
        language_changed: "Язык изменен",
        filters_applied: "Фильтры применены успешно!",
        filters_reset: "Фильтры сброшены",
    },
    
    // 🇦🇿 AZƏRBAYCANCA
    az: {
        // Common
        search: "Axtarış...",
        search_payments: "Ödənişləri axtar...",
        logout: "Çıxış",
        settings: "Parametrlər",
        home: "Əsas",
        save: "Yadda saxla",
        cancel: "Ləğv et",
        apply: "Tətbiq et",
        reset: "Sıfırla",
        show_menu: "Menyunu göstər",
        
        // Login Page
        login_title: "RoyalPark-a xoş gəlmisiniz",
        login_subtitle: "Kommunal xidmətlərin idarə edilməsi sistemi",
        login_select_role: "Rolunuzu seçin",
        username: "İstifadəçi adı",
        username_placeholder: "İstifadəçi adını daxil edin",
        password: "Şifrə",
        password_placeholder: "Şifrəni daxil edin",
        login_button: "Sistemə daxil ol",
        remember_me: "Məni xatırla",
        forgot_password: "Şifrəni unutmusunuz?",
        secure_connection: "Təhlükəsiz bağlantı",
        copyright: "© 2024 RoyalPark. Bütün hüquqlar qorunur.",
        
        // Roles
        role_admin: "Administrator",
        role_user: "Sakin",
        role_maintenance: "Xidmət",
        role_accountant: "Mühasib",
        system_admin: "Sistem admini",
        
        // Navigation Sections
        nav_main: "ƏSAS",
        nav_management: "İDARƏETMƏ",
        nav_finance: "MALİYYƏ",
        nav_maintenance: "XİDMƏT",
        
        // Navigation
        nav_dashboard: "İdarəetmə paneli",
        nav_payments: "Ödənişlər",
        nav_accounts: "Hesablar",
        nav_debts: "Borclar",
        nav_reports: "Hesabatlar",
        nav_financial: "Maliyyə",
        nav_analytics: "Analitika",
        nav_documents: "Sənədlər",
        nav_system: "SİSTEM",
        nav_requests: "Sorğular",
        nav_repair_requests: "Təmir sorğuları",
        nav_meters: "Sayğaclar",
        nav_news: "Xəbərlər",
        nav_profile: "Profil",
        nav_users: "İstifadəçilər",
        nav_buildings: "Binalar",
        nav_apartments: "Mənzillər",
        nav_blocks: "Bloklar",
        nav_tariffs: "Tariflər",
        nav_residents: "Rezidentlər",
        nav_tenants: "Sakinlər",
        nav_readings: "Göstəricilər",
        nav_checks: "Yoxlamalar",
        nav_personnel: "Personal",
        
        // Dashboard
        dashboard_title: "İdarəetmə paneli",
        dashboard_admin: "Administrator paneli",
        dashboard_user: "Sakin paneli",
        dashboard_maintenance: "Xidmət paneli",
        dashboard_accountant: "Mühasib paneli",
        
        // Stats Cards
        income_month: "Aylıq gəlir",
        payments_today: "Bu gün ödənişlər",
        payments_month: "Aylıq ödənişlər",
        debts: "Borclar",
        payability: "Ödəniş qabiliyyəti",
        processed: "İşlənib",
        requires_attention: "Diqqət tələb edir",
        excellent_indicator: "Əla göstərici",
        total_users: "Cəmi istifadəçilər",
        buildings: "Binalar",
        active_requests: "Aktiv sorğular",
        per_month: "aylıq",
        per_week: "həftəlik",
        new: "yeni",
        
        // Time periods
        week: "Həftə",
        month: "Ay",
        year: "İl",
        today: "Bu gün",
        yesterday: "Dünən",
        
        // Days of week
        monday: "B.e",
        tuesday: "Ç.a",
        wednesday: "Ç",
        thursday: "C.a",
        friday: "C",
        saturday: "Ş",
        sunday: "B",
        
        // Activity
        latest_activity: "Son aktivlik",
        latest_payments: "Son ödənişlər",
        new_payment_received: "Yeni ödəniş alındı",
        new_repair_request: "Yeni təmir sorğusu",
        meter_reading: "Sayğac göstəriciləri",
        check_completed: "Yoxlama tamamlandı",
        new_user: "Yeni istifadəçi",
        debt_reminder: "Borc xatırlatması",
        apartment: "Mənzil",
        building: "Bina",
        minutes_ago: "dəqiqə əvvəl",
        hour_ago: "saat əvvəl",
        hours_ago: "saat əvvəl",
        apartments: "mənzil",
        
        // Payment Statistics
        payment_statistics: "Ödəniş statistikası",
        payment_dynamics: "Ödəniş dinamikası",
        
        // Table Headers
        id: "ID",
        user: "İstifadəçi",
        payer: "Ödəyici",
        amount: "Məbləğ",
        date: "Tarix",
        status: "Status",
        status_paid: "Ödənilib",
        status_processing: "İşlənir",
        status_pending: "İşlənir",
        status_failed: "Rədd edilib",
        
        // Filters
        filters_title: "Ödəniş filterləri",
        filter_period: "Dövr",
        filter_status: "Status",
        filter_method: "Ödəniş üsulu",
        filter_building: "Bina",
        all_statuses: "Bütün statuslar",
        all_methods: "Bütün üsullar",
        all_buildings: "Bütün binalar",
        status_paid: "Ödənilib",
        status_pending: "İşlənir",
        status_failed: "Rədd edilib",
        
        // Reports
        reports_title: "Hesabat yaradılması",
        report_financial: "Maliyyə hesabatı",
        report_payments: "Ödənişlər hesabatı",
        report_debts: "Borclar hesabatı",
        report_analytics: "Analitik hesabat",
        report_buildings: "Binalar hesabatı",
        report_tax: "Vergi hesabatı",
        generate: "Yarat",
        generate_all: "Bütün hesabatları yarat",
        
        // Meters
        meters_title: "Sayğacların yoxlanması",
        meter_electricity: "Elektrik",
        meter_cold_water: "Soyuq su",
        meter_hot_water: "İsti su",
        meter_previous: "Əvvəlki",
        meter_current: "Cari",
        meter_consumption: "İstehlak",
        meter_approve: "Təsdiq et",
        meter_reject: "Rədd et",
        meter_investigate: "Araşdır",
        status_pending_check: "Yoxlanılır",
        status_verified: "Yoxlanılıb",
        status_anomaly: "Anomaliya",
        
        // Notifications
        theme_light: "İşıqlı tema",
        theme_dark: "Qaranlıq tema",
        language_changed: "Dil dəyişdirildi",
        filters_applied: "Filterlər uğurla tətbiq edildi!",
        filters_reset: "Filterlər sıfırlandı",
    },
    
    // 🇬🇧 ENGLISH
    en: {
        // Common
        search: "Search...",
        search_payments: "Search payments...",
        logout: "Logout",
        settings: "Settings",
        home: "Home",
        save: "Save",
        cancel: "Cancel",
        apply: "Apply",
        reset: "Reset",
        show_menu: "Show menu",
        
        // Login Page
        login_title: "Welcome to RoyalPark",
        login_subtitle: "Utility Management System",
        login_select_role: "Select your role",
        username: "Username",
        username_placeholder: "Enter username",
        password: "Password",
        password_placeholder: "Enter password",
        login_button: "Sign In",
        remember_me: "Remember me",
        forgot_password: "Forgot password?",
        secure_connection: "Secure connection",
        copyright: "© 2024 RoyalPark. All rights reserved.",
        
        // Roles
        role_admin: "Administrator",
        role_user: "Resident",
        role_maintenance: "Maintenance",
        role_accountant: "Accountant",
        system_admin: "System Admin",
        
        // Navigation Sections
        nav_main: "MAIN",
        nav_management: "MANAGEMENT",
        nav_finance: "FINANCE",
        nav_maintenance: "MAINTENANCE",
        
        // Navigation
        nav_dashboard: "Dashboard",
        nav_payments: "Payments",
        nav_accounts: "Accounts",
        nav_debts: "Debts",
        nav_reports: "Reports",
        nav_financial: "Financial",
        nav_analytics: "Analytics",
        nav_documents: "Documents",
        nav_system: "SYSTEM",
        nav_requests: "Requests",
        nav_repair_requests: "Repair Requests",
        nav_meters: "Meters",
        nav_news: "News",
        nav_profile: "Profile",
        nav_users: "Users",
        nav_buildings: "Buildings",
        nav_apartments: "Apartments",
        nav_blocks: "Blocks",
        nav_tariffs: "Tariffs",
        nav_residents: "Residents",
        nav_tenants: "Tenants",
        nav_readings: "Readings",
        nav_checks: "Checks",
        nav_personnel: "Personnel",
        
        // Dashboard
        dashboard_title: "Dashboard",
        dashboard_admin: "Admin Dashboard",
        dashboard_user: "User Dashboard",
        dashboard_maintenance: "Maintenance Dashboard",
        dashboard_accountant: "Accountant Dashboard",
        
        // Stats Cards
        income_month: "Monthly Income",
        payments_today: "Payments Today",
        payments_month: "Monthly Payments",
        debts: "Debts",
        payability: "Payability",
        processed: "Processed",
        requires_attention: "Requires Attention",
        excellent_indicator: "Excellent Indicator",
        total_users: "Total Users",
        buildings: "Buildings",
        active_requests: "Active Requests",
        per_month: "per month",
        per_week: "per week",
        new: "new",
        
        // Time periods
        week: "Week",
        month: "Month",
        year: "Year",
        today: "Today",
        yesterday: "Yesterday",
        
        // Days of week
        monday: "Mon",
        tuesday: "Tue",
        wednesday: "Wed",
        thursday: "Thu",
        friday: "Fri",
        saturday: "Sat",
        sunday: "Sun",
        
        // Activity
        latest_activity: "Latest Activity",
        latest_payments: "Latest Payments",
        new_payment_received: "New payment received",
        new_repair_request: "New repair request",
        meter_reading: "Meter reading",
        check_completed: "Check completed",
        new_user: "New user",
        debt_reminder: "Debt reminder",
        apartment: "Apartment",
        building: "Building",
        minutes_ago: "minutes ago",
        hour_ago: "hour ago",
        hours_ago: "hours ago",
        apartments: "apartments",
        
        // Payment Statistics
        payment_statistics: "Payment Statistics",
        payment_dynamics: "Payment Dynamics",
        
        // Table Headers
        id: "ID",
        user: "User",
        payer: "Payer",
        amount: "Amount",
        date: "Date",
        status: "Status",
        status_paid: "Paid",
        status_processing: "Processing",
        status_pending: "Pending",
        status_failed: "Failed",
        
        // Filters
        filters_title: "Payment Filters",
        filter_period: "Period",
        filter_status: "Status",
        filter_method: "Payment Method",
        filter_building: "Building",
        all_statuses: "All Statuses",
        all_methods: "All Methods",
        all_buildings: "All Buildings",
        status_paid: "Paid",
        status_pending: "Pending",
        status_failed: "Failed",
        
        // Reports
        reports_title: "Report Generation",
        report_financial: "Financial Report",
        report_payments: "Payments Report",
        report_debts: "Debts Report",
        report_analytics: "Analytics Report",
        report_buildings: "Buildings Report",
        report_tax: "Tax Report",
        generate: "Generate",
        generate_all: "Generate All Reports",
        
        // Meters
        meters_title: "Meters Verification",
        meter_electricity: "Electricity",
        meter_cold_water: "Cold Water",
        meter_hot_water: "Hot Water",
        meter_previous: "Previous",
        meter_current: "Current",
        meter_consumption: "Consumption",
        meter_approve: "Approve",
        meter_reject: "Reject",
        meter_investigate: "Investigate",
        status_pending_check: "Pending Check",
        status_verified: "Verified",
        status_anomaly: "Anomaly",
        
        // Notifications
        theme_light: "Light Theme",
        theme_dark: "Dark Theme",
        language_changed: "Language Changed",
        filters_applied: "Filters applied successfully!",
        filters_reset: "Filters reset",
    }
};

// Language Manager
class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'ru';
        this.init();
    }
    
    init() {
        // Apply saved language on page load
        this.applyLanguage(this.currentLanguage);
        
        // Create language selector if it doesn't exist
        if (!document.querySelector('.language-selector')) {
            this.createLanguageSelector();
        }
    }
    
    createLanguageSelector() {
        const selector = document.createElement('div');
        selector.className = 'language-selector';
        selector.innerHTML = `
            <button class="language-btn" data-lang="ru" title="Русский">
                <span class="flag">🇷🇺</span>
                <span class="lang-code">RU</span>
            </button>
            <button class="language-btn" data-lang="az" title="Azərbaycan">
                <span class="flag">🇦🇿</span>
                <span class="lang-code">AZ</span>
            </button>
            <button class="language-btn" data-lang="en" title="English">
                <span class="flag">🇬🇧</span>
                <span class="lang-code">EN</span>
            </button>
        `;
        
        // Add to top-bar-actions instead of body
        const topBarActions = document.querySelector('.top-bar-actions');
        if (topBarActions) {
            topBarActions.appendChild(selector);
        } else {
            document.body.appendChild(selector);
        }
        
        // Add event listeners
        selector.querySelectorAll('.language-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const lang = btn.getAttribute('data-lang');
                this.changeLanguage(lang);
            });
            
            // Highlight active language
            if (btn.getAttribute('data-lang') === this.currentLanguage) {
                btn.classList.add('active');
            }
        });
    }
    
    changeLanguage(lang) {
        if (!translations[lang]) return;
        
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        
        // Update active button
        document.querySelectorAll('.language-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
        });
        
        // Apply translations
        this.applyLanguage(lang);
        
        // Trigger re-translation of auto-detected elements
        if (window.reapplyAutoTranslations) {
            setTimeout(() => window.reapplyAutoTranslations(), 100);
        }
        
        // Show notification
        this.showNotification(this.translate('language_changed'));
    }
    
    applyLanguage(lang) {
        // Translate all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.translate(key, lang);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.placeholder !== undefined) {
                    element.placeholder = translation;
                }
            } else {
                element.textContent = translation;
            }
        });
        
        // Translate placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.translate(key, lang);
        });
        
        // Translate titles
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.translate(key, lang);
        });
    }
    
    translate(key, lang = null) {
        lang = lang || this.currentLanguage;
        return translations[lang]?.[key] || key;
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'lang-notification';
        notification.innerHTML = `
            <i class="bi bi-translate"></i>
            <span>${message}</span>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: slideInRight 0.3s ease-out;
            z-index: 10000;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.i18n = new LanguageManager();
    });
} else {
    window.i18n = new LanguageManager();
}

