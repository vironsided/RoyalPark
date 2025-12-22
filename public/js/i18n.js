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
        
        // Notifications / Theme
        theme_light: "Светлая тема",
        theme_dark: "Темная тема",
        language_changed: "Язык изменен",
        filters_applied: "Фильтры применены успешно!",
        filters_reset: "Фильтры сброшены",
        user_nav_notifications: "Уведомления",

        // User portal (ЛК жильца)
        user_dashboard_welcome: "Добро пожаловать!",
        user_bills_title: "Мои счета",
        user_bills_status_label: "Статус",
        user_bills_status_all: "Все",
        user_bills_filter_button: "Фильтр",
        user_bills_th_period: "Период",
        user_bills_th_house: "Дом",
        user_bills_th_number: "№",
        user_bills_th_status: "Статус",
        user_bills_th_total: "Итого",
        user_bills_th_paid_remaining: "Оплачено / Остаток",
        user_bills_th_due_date: "Срок оплаты",
        user_bills_th_actions: "Действия",
        user_bills_paid_label: "Оплачено {amount}",
        user_bills_remaining_label: "Остаток {amount}",
        user_bills_open_btn: "Открыть",
        user_bills_pdf_btn: "PDF",

        // User invoice view
        user_invoice_view: "Просмотр счёта",
        user_invoice_back_to_list: "← К списку счетов",
        user_invoice_title_prefix: "Счёт:",
        user_invoice_pdf_button: "PDF",
        user_invoice_house_label: "Дом",
        user_invoice_period_label: "Период",
        user_invoice_status_label: "Статус",
        user_invoice_due_date_label: "Срок оплаты",
        user_invoice_total_label: "Итого",
        user_invoice_payments_title: "Оплаты по счёту",
        user_invoice_payments_th_date: "Дата",
        user_invoice_payments_th_method: "Метод",
        user_invoice_payments_th_amount: "Сумма",
        user_invoice_payments_th_comment: "Комментарий",
        user_invoice_payments_summary: "Оплачено: {paid} · Остаток: {remaining} из {total}",
        user_invoice_items_title: "Описание",
        user_invoice_items_th_description: "Описание",
        user_invoice_items_th_charged: "Начислено",
        user_invoice_items_th_vat: "НДС",
        user_invoice_items_th_total: "Итого",
        user_invoice_items_total_row: "Итого к оплате",
        user_invoice_item_electricity_sample: "Электричество 200.0 кВт·ч",
        user_invoice_item_water_sample: "Вода 300.0 м³",
        
        // User invoice print
        user_invoice_print_title: "Счёт на оплату",
        user_invoice_print_number_label: "№",
        user_invoice_print_resident_label: "Резидент",
        user_invoice_print_period_label: "Период",
        user_invoice_print_status_label: "Статус",
        user_invoice_print_due_date_label: "Срок оплаты",
        user_invoice_print_tariff_label: "Тариф",
        user_invoice_print_total_label: "Сумма к оплате",
        user_invoice_print_payments_title: "Оплата по счёту",
        user_invoice_print_payments_summary: "Оплачено: {paid}, Остаток: {remaining} из {total}",
        user_invoice_print_items_title: "Описание",
        user_invoice_print_generated_prefix: "Квитанция сгенерирована:",
        user_invoice_print_footer_note: "Для печати нажмите кнопку сверху или используйте «Печать в PDF».",
        user_invoice_print_print_button: "Печать",
        user_nav_user_home: "Главная",
        user_nav_user_bills: "Мои счета",
        user_nav_user_report: "Оплатить счета",
        user_nav_user_requests: "Заявки",
        user_nav_user_documents: "Документы",
        user_nav_user_news: "Новости",

        user_appeals_form_title: "Сообщить о проблеме",
        user_appeals_list_title: "Недавние обращения",
        user_appeals_house: "Дом",
        user_appeals_description: "Опишите проблему",
        user_appeals_placeholder: "Например: в доме 12Б не работает уличное освещение...",
        user_appeals_submit: "Отправить",
        user_appeal_modal_title: "Обращение",
        user_appeal_modal_created: "Создано",
        user_appeal_modal_status: "Статус",
        user_appeal_modal_text_label: "Текст обращения",
        user_appeal_modal_edit_label: "Изменить текст обращения",
        user_appeal_modal_edit_hint: "Можно редактировать до прочтения оператором.",
        user_appeal_modal_delete: "Удалить",
        user_appeal_modal_save: "Сохранить",

        // User dashboard main cards/texts
        user_greeting_prefix: "Здравствуйте,",
        user_resident_tag: "Резидент X / 2",
        user_resident_info: "Информация о резиденте",
        user_to_pay_month: "К оплате за месяц",
        user_for_month: "За месяц",
        user_paid_short: "Оплачено",
        user_debt: "Долг по счетам",
        user_advance: "Аванс",
        user_to_pay_now: "К оплате сейчас",
        user_btn_details: "Подробнее",
        user_btn_my_bills: "Мои счета",
        user_btn_report_payment: "Оплатить счета",
        user_btn_pay_from_advance: "Погасить из аванса",
        user_btn_pay_month: "Оплатить за месяц",
        user_btn_pay_all: "Оплатить всё",
        user_balance: "Баланс",
        user_unpaid_bills: "Неоплаченных счета",
        user_requires_payment: "Требует оплаты",
        user_kwh_per_month: "кВт⋅ч за месяц",
        user_electricity: "Электричество",
        user_water_per_month: "м³ за месяц",
        user_water: "Вода",
        user_gas_per_month: "м³ за месяц",
        user_gas: "Газ",
        user_unit_kwh: "кВт·ч",
        user_unit_m3: "м³",
        user_energy_change_month: "-12% за месяц",
        user_active_request: "Активная заявка",
        user_last_bills: "Последние счета",
        user_apartment_label: "Квартира",
        user_bill_electricity: "Электроэнергия",
        user_bill_water: "Водоснабжение",
        user_bill_heating: "Отопление",
        user_bill_utilities: "Коммунальные услуги",
        user_to_pay_status: "К оплате",
        user_quick_actions: "Быстрые действия",
        user_quick_pay_bills: "Оплатить счета",
        user_quick_meters: "Показания счетчиков",
        user_quick_send_data: "Отправить данные",
        user_quick_new_request: "Новая заявка",
        user_quick_report_problem: "Сообщить о проблеме",
        user_quick_documents: "Документы",
        user_quick_view_all: "Посмотреть все",
        user_news_title: "Новости и объявления",
        user_news_1_title: "Плановое отключение воды",
        user_news_1_text: "20 октября с 10:00 до 16:00 будет производиться плановое отключение холодной воды.",
        user_news_1_date: "15.10.2024",
        user_news_2_title: "Новая система оплаты",
        user_news_2_text: "Теперь вы можете оплатить счета через мобильное приложение.",
        user_news_2_date: "10.10.2024",
        user_news_3_title: "Улучшение сервиса",
        user_news_3_text: "Мы обновили наш личный кабинет для вашего удобства!",
        user_news_3_date: "05.10.2024",

        // User report payment
        user_report_title: "Оплатить счета",
        user_report_subtitle: "Укажите данные платежа, чтобы мы могли связать его с вашими счетами.",
        user_report_house_label: "Дом",
        user_report_date_label: "Дата оплаты",
        user_report_date_placeholder: "дд.мм.гггг",
        user_report_amount_label: "Сумма",
        user_report_amount_placeholder: "0.00",
        user_report_method_label: "Метод",
        user_report_reference_label: "№/Референс",
        user_report_reference_placeholder: "номер квитанции/перевода",
        user_report_comment_label: "Комментарий",
        user_report_comment_placeholder: "любая доп. информация",
        user_report_footer_note: "После отправки оператор проверит информацию и применит платёж к вашим счетам.",
        user_report_cancel_btn: "Отмена",
        user_report_submit_btn: "Отправить",

        // Resident detail (meters)
        user_resident_block_label: "Блок",
        user_resident_apartment_label: "Квартира",
        user_resident_status_label: "Статус",
        user_resident_status_active: "Активен",
        user_resident_balance_label: "Баланс",
        user_resident_back_btn: "← Назад",
        user_resident_date_from: "От",
        user_resident_date_to: "До",
        user_resident_filter_btn: "Фильтр",
        user_resident_reset_btn: "Очистить",
        user_resident_quick_select: "Быстрый выбор",
        user_resident_quick_month: "За месяц",
        user_resident_quick_quarter: "За 3 мес.",
        user_resident_quick_half: "За 6 мес.",
        user_resident_quick_year: "За год",
        user_resident_meter_gas: "Газ",
        user_resident_meter_electricity: "Электричество",
        user_resident_meter_water: "Вода",
        user_resident_table_date: "Дата",
        user_resident_table_reading: "Показание",
        user_resident_table_usage: "Расход",
        user_resident_table_charge: "Начислено",
        user_resident_table_vat: "НДС, %",
        user_resident_table_comment: "Комментарий",
        user_resident_table_empty: "Записей пока нет",

        // User appeals extra
        user_appeals_hint: "Максимум 2000 символов.",
        user_appeal_status_read: "Прочитано",
        user_appeal_status_unread: "Не прочитано",
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
        
        // Notifications / Theme
        theme_light: "İşıqlı tema",
        theme_dark: "Qaranlıq tema",
        language_changed: "Dil dəyişdirildi",
        filters_applied: "Filterlər uğurla tətbiq edildi!",
        filters_reset: "Filterlər sıfırlandı",
        user_nav_notifications: "Bildirişlər",

        // User portal (istifadəçi kabineti)
        user_dashboard_welcome: "Xoş gəlmisiniz!",
        user_bills_title: "Mənim hesablarım",
        user_bills_status_label: "Status",
        user_bills_status_all: "Hamısı",
        user_bills_filter_button: "Filter",
        user_bills_th_period: "Dövr",
        user_bills_th_house: "Bina",
        user_bills_th_number: "№",
        user_bills_th_status: "Status",
        user_bills_th_total: "Cəmi",
        user_bills_th_paid_remaining: "Ödənilib / Qalıq",
        user_bills_th_due_date: "Ödəniş müddəti",
        user_bills_th_actions: "Əməliyyatlar",
        user_bills_paid_label: "Ödənilib {amount}",
        user_bills_remaining_label: "Qalıq {amount}",
        user_bills_open_btn: "Aç",
        user_bills_pdf_btn: "PDF",

        // User invoice view
        user_invoice_view: "Hesabın görüntülənməsi",
        user_invoice_back_to_list: "← Hesablar siyahısına",
        user_invoice_title_prefix: "Hesab:",
        user_invoice_pdf_button: "PDF",
        user_invoice_house_label: "Bina",
        user_invoice_period_label: "Dövr",
        user_invoice_status_label: "Status",
        user_invoice_due_date_label: "Ödəniş müddəti",
        user_invoice_total_label: "Cəmi",
        user_invoice_payments_title: "Hesab üzrə ödənişlər",
        user_invoice_payments_th_date: "Tarix",
        user_invoice_payments_th_method: "Metod",
        user_invoice_payments_th_amount: "Məbləğ",
        user_invoice_payments_th_comment: "Şərh",
        user_invoice_payments_summary: "Ödənilib: {paid} · Qalıq: {remaining} / {total}",
        user_invoice_items_title: "Açıqlama",
        user_invoice_items_th_description: "Açıqlama",
        user_invoice_items_th_charged: "Hesablanıb",
        user_invoice_items_th_vat: "ƏDV",
        user_invoice_items_th_total: "Cəmi",
        user_invoice_items_total_row: "Ödəniləcək məbləğ",
        user_invoice_item_electricity_sample: "Elektrik 200.0 kVt·s",
        user_invoice_item_water_sample: "Su 300.0 m³",
        
        // User invoice print
        user_invoice_print_title: "Ödəniş üçün hesab",
        user_invoice_print_number_label: "№",
        user_invoice_print_resident_label: "Rezident",
        user_invoice_print_period_label: "Dövr",
        user_invoice_print_status_label: "Status",
        user_invoice_print_due_date_label: "Ödəniş müddəti",
        user_invoice_print_tariff_label: "Tarif",
        user_invoice_print_total_label: "Ödəniləcək məbləğ",
        user_invoice_print_payments_title: "Hesab üzrə ödənişlər",
        user_invoice_print_payments_summary: "Ödənilib: {paid}, Qalıq: {remaining} / {total}",
        user_invoice_print_items_title: "Açıqlama",
        user_invoice_print_generated_prefix: "Qəbz yaradıldı:",
        user_invoice_print_footer_note: "Çap üçün yuxarıdakı düymədən və ya «PDF-yə çap et» funksiyasından istifadə edin.",
        user_invoice_print_print_button: "Çap et",
        user_nav_user_home: "Əsas səhifə",
        user_nav_user_bills: "Hesablarım",
        user_nav_user_report: "Hesabları ödəmək",
        user_nav_user_requests: "Müraciətlər",
        user_nav_user_documents: "Sənədlər",
        user_nav_user_news: "Xəbərlər",

        user_appeals_form_title: "Problemi bildirin",
        user_appeals_list_title: "Son müraciətlər",
        user_appeals_house: "Bina",
        user_appeals_description: "Problemi təsvir edin",
        user_appeals_placeholder: "Məsələn: 12B binasında küçə işığı işləmir...",
        user_appeals_submit: "Göndər",
        user_appeal_modal_title: "Müraciət",
        user_appeal_modal_created: "Yaradılıb",
        user_appeal_modal_status: "Status",
        user_appeal_modal_text_label: "Müraciət mətni",
        user_appeal_modal_edit_label: "Müraciət mətnini dəyişin",
        user_appeal_modal_edit_hint: "Operator oxuyana qədər redaktə etmək olar.",
        user_appeal_modal_delete: "Sil",
        user_appeal_modal_save: "Yadda saxla",

        // User dashboard main cards/texts
        user_greeting_prefix: "Salam,",
        user_resident_tag: "Sakin X / 2",
        user_resident_info: "Rezident haqqında məlumat",
        user_to_pay_month: "Aylıq ödəniləcək məbləğ",
        user_for_month: "Ay üzrə",
        user_paid_short: "Ödənilib",
        user_debt: "Hesab borcu",
        user_advance: "Avans",
        user_to_pay_now: "İndi ödəniləcək",
        user_btn_details: "Ətraflı",
        user_btn_my_bills: "Hesablarım",
        user_btn_report_payment: "Hesabları ödəmək",
        user_btn_pay_from_advance: "Avansdan ödə",
        user_btn_pay_month: "Ay üçün ödə",
        user_btn_pay_all: "Bütün borcu ödə",
        
        // User report payment
        user_report_title: "Hesabları ödəmək",
        user_report_subtitle: "Ödəniş məlumatlarını daxil edin ki, biz onu hesablarınızla əlaqələndirə bilək.",
        user_report_house_label: "Bina",
        user_report_date_label: "Ödəniş tarixi",
        user_report_date_placeholder: "gg.aa.iiii",
        user_report_amount_label: "Məbləğ",
        user_report_amount_placeholder: "0.00",
        user_report_method_label: "Metod",
        user_report_reference_label: "№/Referans",
        user_report_reference_placeholder: "qəbz / köçürmə nömrəsi",
        user_report_comment_label: "Şərh",
        user_report_comment_placeholder: "istənilən əlavə məlumat",
        user_report_footer_note: "Göndərdikdən sonra operator məlumatı yoxlayacaq və ödənişi hesablarınıza tətbiq edəcək.",
        user_report_cancel_btn: "Ləğv et",
        user_report_submit_btn: "Göndər",
        user_balance: "Balans",
        user_unpaid_bills: "Ödənilməmiş hesablar",
        user_requires_payment: "Ödəniş tələb olunur",
        user_kwh_per_month: "kVt⋅s ay üzrə",
        user_electricity: "Elektrik",
        user_water_per_month: "m³ ay üzrə",
        user_water: "Su",
        user_gas_per_month: "m³ ay üzrə",
        user_gas: "Qaz",
        user_unit_kwh: "kVt·s",
        user_unit_m3: "m³",
        user_energy_change_month: "ay ərzində -12%",
        user_active_request: "Aktiv müraciət",
        user_last_bills: "Son hesablar",
        user_apartment_label: "Mənzil",
        user_bill_electricity: "Elektrik enerjisi",
        user_bill_water: "Su təchizatı",
        user_bill_heating: "İstilik",
        user_bill_utilities: "Kommunal xidmətlər",
        user_to_pay_status: "Ödənilməlidir",
        user_quick_actions: "Sürətli əməliyyatlar",
        user_quick_pay_bills: "Hesabları ödə",
        user_quick_meters: "Sayğac göstəriciləri",
        user_quick_send_data: "Məlumatları göndər",
        user_quick_new_request: "Yeni müraciət",
        user_quick_report_problem: "Problemi bildirin",
        user_quick_documents: "Sənədlər",
        user_quick_view_all: "Hamısına bax",
        user_news_title: "Xəbərlər və elanlar",
        user_news_1_title: "Su təchizatının planlı dayandırılması",
        user_news_1_text: "20 oktyabr tarixində saat 10:00-dan 16:00-dək soyuq suyun verilişi planlı şəkildə dayandırılacaq.",
        user_news_1_date: "15.10.2024",
        user_news_2_title: "Yeni ödəniş sistemi",
        user_news_2_text: "Artıq hesablarınızı mobil tətbiq vasitəsilə də ödəyə bilərsiniz.",
        user_news_2_date: "10.10.2024",
        user_news_3_title: "Xidmətin təkmilləşdirilməsi",
        user_news_3_text: "Sizin rahatlığınız üçün şəxsi kabinetimizi yeniləmişik!",
        user_news_3_date: "05.10.2024",

        // Resident detail (meters)
        user_resident_block_label: "Blok",
        user_resident_apartment_label: "Mənzil",
        user_resident_status_label: "Status",
        user_resident_status_active: "Aktivdir",
        user_resident_balance_label: "Balans",
        user_resident_back_btn: "← Geri",
        user_resident_date_from: "Kimdən",
        user_resident_date_to: "Kimə",
        user_resident_filter_btn: "Filter",
        user_resident_reset_btn: "Təmizlə",
        user_resident_quick_select: "Sürətli seçim",
        user_resident_quick_month: "Ay üzrə",
        user_resident_quick_quarter: "3 ay",
        user_resident_quick_half: "6 ay",
        user_resident_quick_year: "İl üzrə",
        user_resident_meter_gas: "Qaz",
        user_resident_meter_electricity: "Elektrik",
        user_resident_meter_water: "Su",
        user_resident_table_date: "Tarix",
        user_resident_table_reading: "Göstərici",
        user_resident_table_usage: "İstifadə",
        user_resident_table_charge: "Hesablanıb",
        user_resident_table_vat: "ƏDV, %",
        user_resident_table_comment: "Şərh",
        user_resident_table_empty: "Hələ ki, qeyd yoxdur",

        // User appeals extra
        user_appeals_hint: "Maksimum 2000 simvol.",
        user_appeal_status_read: "Oxunub",
        user_appeal_status_unread: "Oxunmayıb",
    },
    
    // en ENGLISH
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
        
        // Notifications / Theme
        theme_light: "Light Theme",
        theme_dark: "Dark Theme",
        language_changed: "Language Changed",
        filters_applied: "Filters applied successfully!",
        filters_reset: "Filters reset",
        user_nav_notifications: "Notifications",

        // User portal
        user_dashboard_welcome: "Welcome!",
        user_bills_title: "My bills",
        user_bills_status_label: "Status",
        user_bills_status_all: "All",
        user_bills_filter_button: "Filter",
        user_bills_th_period: "Period",
        user_bills_th_house: "Building",
        user_bills_th_number: "No.",
        user_bills_th_status: "Status",
        user_bills_th_total: "Total",
        user_bills_th_paid_remaining: "Paid / Remaining",
        user_bills_th_due_date: "Due date",
        user_bills_th_actions: "Actions",
        user_bills_paid_label: "Paid {amount}",
        user_bills_remaining_label: "Remaining {amount}",
        user_bills_open_btn: "Open",
        user_bills_pdf_btn: "PDF",

        // User invoice view
        user_invoice_view: "Invoice View",
        user_invoice_back_to_list: "← Back to bills list",
        user_invoice_title_prefix: "Invoice:",
        user_invoice_pdf_button: "PDF",
        user_invoice_house_label: "Building",
        user_invoice_period_label: "Period",
        user_invoice_status_label: "Status",
        user_invoice_due_date_label: "Due date",
        user_invoice_total_label: "Total",
        user_invoice_payments_title: "Payments for invoice",
        user_invoice_payments_th_date: "Date",
        user_invoice_payments_th_method: "Method",
        user_invoice_payments_th_amount: "Amount",
        user_invoice_payments_th_comment: "Comment",
        user_invoice_payments_summary: "Paid: {paid} · Remaining: {remaining} of {total}",
        user_invoice_items_title: "Description",
        user_invoice_items_th_description: "Description",
        user_invoice_items_th_charged: "Charged",
        user_invoice_items_th_vat: "VAT",
        user_invoice_items_th_total: "Total",
        user_invoice_items_total_row: "Total to pay",
        user_invoice_item_electricity_sample: "Electricity 200.0 kWh",
        user_invoice_item_water_sample: "Water 300.0 m³",
        
        // User invoice print
        user_invoice_print_title: "Invoice",
        user_invoice_print_number_label: "No.",
        user_invoice_print_resident_label: "Resident",
        user_invoice_print_period_label: "Period",
        user_invoice_print_status_label: "Status",
        user_invoice_print_due_date_label: "Due date",
        user_invoice_print_tariff_label: "Tariff",
        user_invoice_print_total_label: "Total amount",
        user_invoice_print_payments_title: "Payments for invoice",
        user_invoice_print_payments_summary: "Paid: {paid}, Remaining: {remaining} of {total}",
        user_invoice_print_items_title: "Description",
        user_invoice_print_generated_prefix: "Receipt generated:",
        user_invoice_print_footer_note: "To print, click the button above or use \"Print to PDF\".",
        user_invoice_print_print_button: "Print",
        user_nav_user_home: "Home",
        user_nav_user_bills: "My bills",
        user_nav_user_report: "Pay bills",
        user_nav_user_requests: "Requests",
        user_nav_user_documents: "Documents",
        user_nav_user_news: "News",

        user_appeals_form_title: "Report a problem",
        user_appeals_list_title: "Recent requests",
        user_appeals_house: "Building",
        user_appeals_description: "Describe the issue",
        user_appeals_placeholder: "For example: the street light is not working near entrance 12B...",
        user_appeals_submit: "Submit",
        user_appeal_modal_title: "Request",
        user_appeal_modal_created: "Created",
        user_appeal_modal_status: "Status",
        user_appeal_modal_text_label: "Request text",
        user_appeal_modal_edit_label: "Edit request text",
        user_appeal_modal_edit_hint: "Can be edited until an operator reads it.",
        user_appeal_modal_delete: "Delete",
        user_appeal_modal_save: "Save",

        // User dashboard main cards/texts
        user_greeting_prefix: "Hello,",
        user_resident_tag: "Resident X / 2",
        user_resident_info: "Resident Information",
        user_to_pay_month: "Amount due this month",
        user_for_month: "This month",
        user_paid_short: "Paid",
        user_debt: "Debt by bills",
        user_advance: "Advance",
        user_to_pay_now: "Due now",
        user_btn_details: "Details",
        user_btn_my_bills: "My bills",
        user_btn_report_payment: "Pay bills",
        user_btn_pay_from_advance: "Pay from advance",
        user_btn_pay_month: "Pay for month",
        user_btn_pay_all: "Pay all",
        user_balance: "Balance",
        user_unpaid_bills: "Unpaid bills",
        user_requires_payment: "Requires payment",
        user_kwh_per_month: "kWh per month",
        user_electricity: "Electricity",
        user_water_per_month: "m³ per month",
        user_water: "Water",
        user_gas_per_month: "m³ per month",
        user_gas: "Gas",
        user_unit_kwh: "kWh",
        user_unit_m3: "m³",
        user_energy_change_month: "-12% per month",
        user_active_request: "Active request",
        user_last_bills: "Latest bills",
        user_apartment_label: "Apartment",
        user_bill_electricity: "Electricity",
        user_bill_water: "Water supply",
        user_bill_heating: "Heating",
        user_bill_utilities: "Utility services",
        user_to_pay_status: "To pay",
        user_quick_actions: "Quick actions",
        user_quick_pay_bills: "Pay bills",
        user_quick_meters: "Meter readings",
        user_quick_send_data: "Send data",
        user_quick_new_request: "New request",
        user_quick_report_problem: "Report a problem",
        user_quick_documents: "Documents",
        user_quick_view_all: "View all",
        user_news_title: "News & announcements",
        user_news_1_title: "Planned water outage",
        user_news_1_text: "On October 20 from 10:00 to 16:00 there will be a planned shutdown of cold water supply.",
        user_news_1_date: "15.10.2024",
        user_news_2_title: "New payment system",
        user_news_2_text: "You can now pay your bills via the mobile application.",
        user_news_2_date: "10.10.2024",
        user_news_3_title: "Service improvement",
        user_news_3_text: "We have updated your personal cabinet for your convenience!",
        user_news_3_date: "05.10.2024",

        // User report payment
        user_report_title: "Pay bills",
        user_report_subtitle: "Enter payment details so we can match it with your bills.",
        user_report_house_label: "Building",
        user_report_date_label: "Payment date",
        user_report_date_placeholder: "dd.mm.yyyy",
        user_report_amount_label: "Amount",
        user_report_amount_placeholder: "0.00",
        user_report_method_label: "Method",
        user_report_reference_label: "No./Reference",
        user_report_reference_placeholder: "receipt / transfer number",
        user_report_comment_label: "Comment",
        user_report_comment_placeholder: "any additional information",
        user_report_footer_note: "After submission, an operator will verify the information and apply the payment to your bills.",
        user_report_cancel_btn: "Cancel",
        user_report_submit_btn: "Submit",

        // Resident detail (meters)
        user_resident_block_label: "Block",
        user_resident_apartment_label: "Apartment",
        user_resident_status_label: "Status",
        user_resident_status_active: "Active",
        user_resident_balance_label: "Balance",
        user_resident_back_btn: "← Back",
        user_resident_date_from: "From",
        user_resident_date_to: "To",
        user_resident_filter_btn: "Filter",
        user_resident_reset_btn: "Reset",
        user_resident_quick_select: "Quick select",
        user_resident_quick_month: "For month",
        user_resident_quick_quarter: "For 3 months",
        user_resident_quick_half: "For 6 months",
        user_resident_quick_year: "For year",
        user_resident_meter_gas: "Gas",
        user_resident_meter_electricity: "Electricity",
        user_resident_meter_water: "Water",
        user_resident_table_date: "Date",
        user_resident_table_reading: "Reading",
        user_resident_table_usage: "Usage",
        user_resident_table_charge: "Charged",
        user_resident_table_vat: "VAT, %",
        user_resident_table_comment: "Comment",
        user_resident_table_empty: "No records yet",

        // User appeals extra
        user_appeals_hint: "Maximum 2000 characters.",
        user_appeal_status_read: "Read",
        user_appeal_status_unread: "Unread",
    }
};

// Сделаем объект translations доступным глобально (для печатных шаблонов и др.)
if (typeof window !== 'undefined') {
    window.translations = translations;
}

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
                <span class="lang-code">RU</span>
            </button>
            <button class="language-btn" data-lang="az" title="Azərbaycan">
                <span class="lang-code">AZ</span>
            </button>
            <button class="language-btn" data-lang="en" title="English">
                <span class="lang-code">EN</span>
            </button>
        `;
        
        // Add to top-bar-actions instead of body
        const topBarActions = document.querySelector('.top-bar-actions');
        if (topBarActions) {
            // Ставим переключатель языка перед профилем пользователя,
            // чтобы визуальный порядок совпадал с макетом.
            const profile = topBarActions.querySelector('.user-profile');
            if (profile) {
                topBarActions.insertBefore(selector, profile);
            } else {
                topBarActions.appendChild(selector);
            }
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
        // Update current language
        this.currentLanguage = lang;
        
        // Translate all elements with data-i18n attribute
        // Search in main document (covers everything including SPA content)
        const containers = [document];
        
        containers.forEach(container => {
            if (!container) return;
            
            // Get all elements with data-i18n, process from deepest to shallowest
            const allElements = Array.from(container.querySelectorAll('[data-i18n]'));
            // Sort by depth (deepest first) to avoid updating parents before children
            allElements.sort((a, b) => {
                const depthA = (a.parentElement ? a.parentElement.querySelectorAll('[data-i18n]').length : 0);
                const depthB = (b.parentElement ? b.parentElement.querySelectorAll('[data-i18n]').length : 0);
                return depthB - depthA;
            });
            
            allElements.forEach(element => {
                const key = element.getAttribute('data-i18n');
                if (!key) return;
                
                const translation = this.translate(key, lang);
                
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    if (element.placeholder !== undefined) {
                        element.placeholder = translation;
                    }
                } else {
                    // Check if element has any child with data-i18n attribute
                    const childWithI18n = element.querySelector(':scope > [data-i18n]');
                    
                    if (childWithI18n) {
                        // Parent has direct child with data-i18n, skip parent
                        // Child will be processed in its own iteration
                        return;
                    }
                    
                    // Save non-i18n children that should be preserved (like .meter-head-unit)
                    const preserveChildren = Array.from(element.children).filter(child => 
                        child.classList.contains('meter-head-unit') || 
                        child.classList.contains('meter-unit')
                    );
                    
                    if (preserveChildren.length > 0) {
                        // Store children temporarily
                        const childrenData = preserveChildren.map(child => ({
                            element: child,
                            html: child.outerHTML
                        }));
                        
                        // Update text content
                        element.textContent = translation;
                        
                        // Restore preserved children
                        childrenData.forEach(({ element: child, html }) => {
                            const temp = document.createElement('div');
                            temp.innerHTML = html;
                            element.appendChild(temp.firstElementChild);
                        });
                    } else {
                        // Simple case: just update textContent
                        element.textContent = translation;
                    }
                }
            });
            
            // Translate placeholders
            container.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
                const key = element.getAttribute('data-i18n-placeholder');
                if (key) {
                    element.placeholder = this.translate(key, lang);
                }
            });
            
            // Translate titles
            container.querySelectorAll('[data-i18n-title]').forEach(element => {
                const key = element.getAttribute('data-i18n-title');
                if (key) {
                    element.title = this.translate(key, lang);
                }
            });
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

