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
        
        // Account settings
        account_settings_title: "Настройки аккаунта",
        account_tab_profile: "Профиль",
        account_tab_password: "Пароль",
        account_full_name: "Ф.И.О.",
        account_full_name_placeholder: "Введите Ф.И.О.",
        account_phone: "Телефон",
        account_phone_placeholder: "Номер телефона",
        account_email: "E-mail",
        account_email_placeholder: "E-mail",
        account_avatar: "Аватар",
        account_file_select_btn: "Выбор файла",
        account_file_no_selected: "Не выбран ни один файл",
        account_interface_language: "Язык интерфейса",
        account_avatar_hint: "PNG/JPG/WebP, до 4 МБ.",
        account_save_changes: "Сохранить изменения",
        account_current_password: "Текущий пароль",
        account_current_password_placeholder: "Введите текущий пароль",
        account_new_password: "Новый пароль",
        account_new_password_placeholder: "Введите новый пароль",
        account_confirm_password: "Подтвердите пароль",
        account_confirm_password_placeholder: "Подтвердите новый пароль",
        account_change_password: "Изменить пароль",
        account_saving: "Сохранение...",
        error_loading_data: "Ошибка загрузки данных",
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
        
        // News Management
        admin_news_title: "Управление новостями",
        admin_news_subtitle: "Создавайте и редактируйте новости для пользователей на 3 языках",
        admin_news_create_btn: "Создать новость",
        admin_news_th_icon: "Иконка",
        admin_news_th_title: "Заголовок",
        admin_news_th_priority: "Приоритет",
        admin_news_th_published: "Опубликовано",
        admin_news_th_status: "Статус",
        admin_news_th_actions: "Действия",
        admin_news_status_active: "Активна",
        admin_news_status_inactive: "Неактивна",
        admin_news_modal_create: "Создать новость",
        admin_news_modal_edit: "Редактировать новость",
        admin_news_label_icon: "Иконка",
        admin_news_label_priority: "Приоритет",
        admin_news_label_priority_hint: "Чем выше, тем важнее",
        admin_news_label_published_at: "Дата публикации",
        admin_news_label_expires_at: "Срок действия",
        admin_news_label_expires_hint: "Оставьте пустым для бессрочной",
        admin_news_label_active: "Активна (видна пользователям)",
        admin_news_label_content: "Описание",
        admin_news_icon_info: "Информация",
        admin_news_icon_announcement: "Объявление",
        admin_news_icon_star: "Важное",
        admin_news_icon_warning: "Предупреждение",
        admin_news_icon_calendar: "Событие",
        admin_news_icon_tools: "Техработы",
        
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
        status_draft: "Черновик",
        status_issued: "Выставлен",
        status_partial: "Частично оплачен",
        status_overpaid: "Переплата",
        status_canceled: "Отменен",
        
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
        meter_cold_water: "Вода",
        meter_hot_water: "Горячая вода",
        meter_gas: "Газ",
        meter_sewerage: "Канализация",
        meter_previous: "Предыдущее",
        meter_current: "Текущее",
        meter_consumption: "Потребление",
        stable_tariff: "Стабильный тариф",
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
        notifications: "Уведомления",
        notifications_empty: "Нет уведомлений",
        notifications_load_error: "Не удалось загрузить уведомления",
        notifications_badge_new: "НОВАЯ",
        notification_invoice_issued: "Выставлен счет для {house_info}. Сумма: {amount}. Период: {period}. Оплатить с {from_date} по {to_date}",

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
        invoice_payments_empty: "Оплаты по этому счёту отсутствуют.",
        user_invoice_payments_th_date: "Дата",
        user_invoice_payments_th_method: "Метод",
        user_invoice_payments_th_amount: "Сумма",
        user_invoice_payments_th_comment: "Комментарий",
        user_invoice_payment_method_advance: "Аванс",
        user_invoice_payments_summary: "Оплачено: {paid} · Остаток: {remaining} из {total}",
        user_invoice_pay_btn: "Оплатить",
        user_invoice_items_title: "Описание",
        user_invoice_items_th_description: "Описание",
        user_invoice_items_th_consumed: "Израсходовано",
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
        
        // Payment page
        payment_select_method: "Выберите способ оплаты",
        payment_add_new_card: "Добавить новую",
        payment_card_payment: "Оплата банковской картой",
        payment_amount_label: "Сумма к оплате",
        payment_card_number: "Номер карты",
        payment_card_number_placeholder: "2324 5566 6677 7898",
        payment_card_name: "Имя на карте",
        payment_card_name_placeholder: "Имя Фамилия",
        payment_card_expiry: "Срок действия",
        payment_card_expiry_placeholder: "11/25",
        payment_card_cvv: "CVV",
        payment_card_cvv_placeholder: "123",
        payment_save_card: "Сохранить карту",
        payment_pay_button: "Оплатить",
        payment_details_title: "Детали оплаты",
        payment_order_subtitle: "Оплата счёта",
        payment_type_label: "Тип платежа",
        payment_resident_label: "Резидент",
        payment_period_label: "Период",
        payment_invoice_label: "Счёт",
        payment_total_label: "Итого",
        payment_custom_amount: "Указать другую сумму для оплаты",
        payment_custom_amount_label: "Сумма к оплате",
        payment_topup_advance_btn: "Пополнить аванс",
        payment_cancel_topup_btn: "Отменить пополнение",
        payment_topup_advance_label: "Пополнение аванса",
        payment_time_expired: "Время на оплату истекло. Данные очищены, начните заново.",
        payment_time_remaining: "Время на оплату",
        payment_all_debt: "Оплата всего долга",
        payment_current_month: "Оплата за текущий месяц",
        payment_full_debt: "Полное погашение долга по счетам",
        payment_month_bills: "Оплата счетов за текущий месяц",
        payment_invoice_payment: "Оплата счёта",
        payment_multiple_invoices: "Несколько счетов",
        payment_bank_label: "Банк",
        payment_card_holder_name: "Имя держателя карты",
        payment_expiry_date: "Срок действия",
        payment_authorized_signature: "Authorized Signature",
        payment_card_property: "This card is property of the issuer.",
        payment_advance_balance: "Баланс аванса",
        payment_resident_name: "Имя резидента",
        payment_valid_thru: "Действительно до",
        payment_resident_pass: "КАРТА РЕЗИДЕНТА",
        
        // Payment comments
        payment_comment_new_card: "Оплата новой картой ****{last4}",
        payment_comment_advance: "Списание из аванса Royal Park Pass",
        payment_comment_saved_card: "Оплата картой {brand} {suffix}",
        payment_comment_online: "Онлайн-оплата",
        
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
        user_resident_tag: "Резидент",
        user_resident_info: "Информация о резиденте",
        user_to_pay_month: "К оплате за месяц",
        user_for_month: "За месяц",
        user_paid_short: "Оплачено",
        user_debt: "Долг по счетам",
        user_advance: "Аванс",
        user_to_pay_now: "К оплате сейчас",
        user_btn_details: "Подробнее",
        user_btn_my_bills: "Мои счета",
        user_btn_report_payment: "Оплатить неоплаченные счета",
        user_btn_pay_from_advance: "Погасить из аванса",
        user_btn_pay_month: "Оплатить за месяц",
        user_btn_pay_all: "Оплатить всё",
        user_balance: "Баланс",
        user_unpaid_bills: "Неоплаченных счета",
        user_unpaid_count: "неоплаченных",
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
        user_quick_documents: "Новости",
        user_quick_view_all: "Посмотреть все",
        user_news_title: "Новости и объявления",
        user_no_news: "Нет новостей",
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
        
        // Pagination
        pagination_page: "Стр.",
        pagination_of: "из",
        pagination_total: "всего",
        pagination_on: "На",
        pagination_per_page: "странице:",
        
        // Additional labels
        user_personal_account: "Личный кабинет",
        user_due_date_prefix: "Срок оплаты:",
        
        // Months
        month_january: "Январь",
        month_february: "Февраль",
        month_march: "Март",
        month_april: "Апрель",
        month_may: "Май",
        month_june: "Июнь",
        month_july: "Июль",
        month_august: "Август",
        month_september: "Сентябрь",
        month_october: "Октябрь",
        month_november: "Ноябрь",
        month_december: "Декабрь",
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
        
        // Account settings
        account_settings_title: "Hesab parametrləri",
        account_tab_profile: "Profil",
        account_tab_password: "Şifrə",
        account_full_name: "Ad Soyad",
        account_full_name_placeholder: "Ad Soyad daxil edin",
        account_phone: "Telefon",
        account_phone_placeholder: "Telefon nömrəsi",
        account_email: "E-mail",
        account_email_placeholder: "E-mail",
        account_avatar: "Avatar",
        account_file_select_btn: "Fayl seç",
        account_file_no_selected: "Heç bir fayl seçilməyib",
        account_interface_language: "İnterfeys dili",
        account_avatar_hint: "PNG/JPG/WebP, maksimum 4 MB.",
        account_save_changes: "Dəyişiklikləri yadda saxla",
        account_current_password: "Cari şifrə",
        account_current_password_placeholder: "Cari şifrəni daxil edin",
        account_new_password: "Yeni şifrə",
        account_new_password_placeholder: "Yeni şifrəni daxil edin",
        account_confirm_password: "Şifrəni təsdiqləyin",
        account_confirm_password_placeholder: "Yeni şifrəni təsdiqləyin",
        account_change_password: "Şifrəni dəyiş",
        account_saving: "Yadda saxlanılır...",
        error_loading_data: "Məlumat yüklənmədi",
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
        
        // News Management
        admin_news_title: "Xəbərlərin idarə edilməsi",
        admin_news_subtitle: "İstifadəçilər üçün 3 dildə xəbərlər yaradın və redaktə edin",
        admin_news_create_btn: "Xəbər yarat",
        admin_news_th_icon: "İkona",
        admin_news_th_title: "Başlıq",
        admin_news_th_priority: "Prioritet",
        admin_news_th_published: "Dərc edilib",
        admin_news_th_status: "Status",
        admin_news_th_actions: "Əməliyyatlar",
        admin_news_status_active: "Aktiv",
        admin_news_status_inactive: "Deaktiv",
        admin_news_modal_create: "Xəbər yarat",
        admin_news_modal_edit: "Xəbəri redaktə et",
        admin_news_label_icon: "İkona",
        admin_news_label_priority: "Prioritet",
        admin_news_label_priority_hint: "Nə qədər yüksəkdirsə, o qədər vacibdir",
        admin_news_label_published_at: "Dərc tarixi",
        admin_news_label_expires_at: "Bitmə tarixi",
        admin_news_label_expires_hint: "Müddətsiz üçün boş qoyun",
        admin_news_label_active: "Aktiv (istifadəçilərə görünür)",
        admin_news_label_content: "Təsvir",
        admin_news_icon_info: "Məlumat",
        admin_news_icon_announcement: "Elan",
        admin_news_icon_star: "Vacib",
        admin_news_icon_warning: "Xəbərdarlıq",
        admin_news_icon_calendar: "Hadisə",
        admin_news_icon_tools: "Texniki işlər",
        
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
        status_draft: "Qaralama",
        status_issued: "Verilmiş",
        status_partial: "Qismən ödənilib",
        status_overpaid: "Artıq ödəniş",
        status_canceled: "Ləğv edilib",
        
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
        meter_cold_water: "Su",
        meter_hot_water: "İsti su",
        meter_gas: "Qaz",
        meter_sewerage: "Kanalizasiya",
        meter_previous: "Əvvəlki",
        meter_current: "Cari",
        meter_consumption: "İstehlak",
        stable_tariff: "Sabit tarif",
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
        notifications: "Bildirişlər",
        notifications_empty: "Bildiriş yoxdur",
        notifications_load_error: "Bildirişləri yükləmək mümkün olmadı",
        notifications_badge_new: "YENİ",
        notification_invoice_issued: "Blok {house_info} üçün hesab tərtib edilib. Məbləğ: {amount}. Dövr: {period}. Ödəniş {from_date} - {to_date} tarixləri arasında mümkündür",

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
        invoice_payments_empty: "Bu hesab üzrə ödənişlər yoxdur.",
        user_invoice_items_empty: "Pozisiyalar yoxdur",
        user_invoice_payments_th_date: "Tarix",
        user_invoice_payments_th_method: "Metod",
        user_invoice_payments_th_amount: "Məbləğ",
        user_invoice_payments_th_comment: "Şərh",
        user_invoice_payment_method_advance: "Avans",
        user_invoice_payments_summary: "Ödənilib: {paid} · Qalıq: {remaining} / {total}",
        user_invoice_pay_btn: "Ödəmək",
        user_invoice_items_title: "Açıqlama",
        user_invoice_items_th_description: "Açıqlama",
        user_invoice_items_th_consumed: "İstehlak",
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
        user_resident_tag: "Sakin",
        user_resident_info: "Rezident haqqında məlumat",
        user_to_pay_month: "Aylıq ödəniləcək məbləğ",
        user_for_month: "Ay üzrə",
        user_paid_short: "Ödənilib",
        user_debt: "Hesab borcu",
        user_advance: "Avans",
        user_to_pay_now: "İndi ödəniləcək",
        user_btn_details: "Ətraflı",
        user_btn_my_bills: "Hesablarım",
        user_btn_report_payment: "Ödənilməmiş hesabları ödəmək",
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
        
        // Payment page
        payment_select_method: "Ödəniş üsulunu seçin",
        payment_add_new_card: "Yeni əlavə et",
        payment_card_payment: "Bank kartı ilə ödəniş",
        payment_amount_label: "Ödəniləcək məbləğ",
        payment_card_number: "Kart nömrəsi",
        payment_card_number_placeholder: "2324 5566 6677 7898",
        payment_card_name: "Kartdakı ad",
        payment_card_name_placeholder: "Ad Soyad",
        payment_card_expiry: "Etibarlılıq müddəti",
        payment_card_expiry_placeholder: "11/25",
        payment_card_cvv: "CVV",
        payment_card_cvv_placeholder: "123",
        payment_save_card: "Kartı yadda saxla",
        payment_pay_button: "Ödə",
        payment_details_title: "Ödəniş detalları",
        payment_order_subtitle: "Hesab ödənişi",
        payment_type_label: "Ödəniş növü",
        payment_resident_label: "Rezident",
        payment_period_label: "Dövr",
        payment_invoice_label: "Hesab",
        payment_total_label: "Cəmi",
        payment_custom_amount: "Ödəniş üçün başqa məbləğ göstər",
        payment_custom_amount_label: "Ödəniləcək məbləğ",
        payment_topup_advance_btn: "Avansı artır",
        payment_cancel_topup_btn: "Avans artırmanı ləğv et",
        payment_topup_advance_label: "Avansın artırılması",
        payment_time_expired: "Ödəniş müddəti bitdi. Məlumatlar təmizləndi, yenidən başlayın.",
        payment_time_remaining: "Ödəniş müddəti",
        payment_all_debt: "Bütün borcun ödənilməsi",
        payment_current_month: "Cari ay üçün ödəniş",
        payment_full_debt: "Hesablar üzrə borcun tam ödənilməsi",
        payment_month_bills: "Cari ay üçün hesabların ödənilməsi",
        payment_invoice_payment: "Hesab ödənişi",
        payment_multiple_invoices: "Bir neçə hesab",
        payment_bank_label: "Bank",
        payment_card_holder_name: "Kart sahibinin adı",
        payment_expiry_date: "Etibarlılıq müddəti",
        payment_authorized_signature: "Rəsmi imza",
        payment_card_property: "Bu kart emitentə məxsusdur.",
        payment_advance_balance: "Avans balansı",
        payment_resident_pass: "REZİDENT KARTI",
        
        // Payment comments
        payment_comment_new_card: "Yeni kartla ödəniş ****{last4}",
        payment_comment_advance: "Royal Park Pass avansından çıxarış",
        payment_comment_saved_card: "{brand} {suffix} kartı ilə ödəniş",
        payment_comment_online: "Onlayn ödəniş",
        payment_resident_name: "Rezident adı",
        payment_valid_thru: "Etibarlılıq müddəti",
        
        user_balance: "Balans",
        user_unpaid_bills: "Ödənilməmiş hesablar",
        user_unpaid_count: "ödənilməmiş",
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
        user_quick_documents: "Xəbərlər",
        user_quick_view_all: "Hamısına bax",
        user_news_title: "Xəbərlər və elanlar",
        user_no_news: "Xəbər yoxdur",
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
        
        // Pagination
        pagination_page: "Səh.",
        pagination_of: "dən",
        pagination_total: "cəmi",
        pagination_on: "Hər",
        pagination_per_page: "səhifədə:",
        
        // Additional labels
        user_personal_account: "Şəxsi kabinet",
        user_due_date_prefix: "Ödəniş müddəti:",
        
        // Months
        month_january: "Yanvar",
        month_february: "Fevral",
        month_march: "Mart",
        month_april: "Aprel",
        month_may: "May",
        month_june: "İyun",
        month_july: "İyul",
        month_august: "Avqust",
        month_september: "Sentyabr",
        month_october: "Oktyabr",
        month_november: "Noyabr",
        month_december: "Dekabr",
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
        
        // Account settings
        account_settings_title: "Account Settings",
        account_tab_profile: "Profile",
        account_tab_password: "Password",
        account_full_name: "Full Name",
        account_full_name_placeholder: "Enter full name",
        account_phone: "Phone",
        account_phone_placeholder: "Phone number",
        account_email: "E-mail",
        account_email_placeholder: "E-mail",
        account_avatar: "Avatar",
        account_file_select_btn: "Choose file",
        account_file_no_selected: "No file selected",
        account_interface_language: "Interface Language",
        account_avatar_hint: "PNG/JPG/WebP, up to 4 MB.",
        account_save_changes: "Save Changes",
        account_current_password: "Current Password",
        account_current_password_placeholder: "Enter current password",
        account_new_password: "New Password",
        account_new_password_placeholder: "Enter new password",
        account_confirm_password: "Confirm Password",
        account_confirm_password_placeholder: "Confirm new password",
        account_change_password: "Change Password",
        account_saving: "Saving...",
        error_loading_data: "Error loading data",
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
        
        // News Management
        admin_news_title: "News Management",
        admin_news_subtitle: "Create and edit news for users in 3 languages",
        admin_news_create_btn: "Create News",
        admin_news_th_icon: "Icon",
        admin_news_th_title: "Title",
        admin_news_th_priority: "Priority",
        admin_news_th_published: "Published",
        admin_news_th_status: "Status",
        admin_news_th_actions: "Actions",
        admin_news_status_active: "Active",
        admin_news_status_inactive: "Inactive",
        admin_news_modal_create: "Create News",
        admin_news_modal_edit: "Edit News",
        admin_news_label_icon: "Icon",
        admin_news_label_priority: "Priority",
        admin_news_label_priority_hint: "Higher is more important",
        admin_news_label_published_at: "Publish Date",
        admin_news_label_expires_at: "Expiry Date",
        admin_news_label_expires_hint: "Leave empty for permanent",
        admin_news_label_active: "Active (visible to users)",
        admin_news_label_content: "Description",
        admin_news_icon_info: "Information",
        admin_news_icon_announcement: "Announcement",
        admin_news_icon_star: "Important",
        admin_news_icon_warning: "Warning",
        admin_news_icon_calendar: "Event",
        admin_news_icon_tools: "Maintenance",
        
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
        status_draft: "Draft",
        status_issued: "Issued",
        status_partial: "Partially paid",
        status_overpaid: "Overpaid",
        status_canceled: "Canceled",
        
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
        meter_cold_water: "Water",
        meter_hot_water: "Hot Water",
        meter_gas: "Gas",
        meter_sewerage: "Sewerage",
        meter_previous: "Previous",
        meter_current: "Current",
        meter_consumption: "Consumption",
        stable_tariff: "Stable tariff",
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
        notifications: "Notifications",
        notifications_empty: "No notifications",
        notifications_load_error: "Failed to load notifications",
        notifications_badge_new: "NEW",
        notification_invoice_issued: "Invoice issued for {house_info}. Amount: {amount}. Period: {period}. Pay between {from_date} and {to_date}",

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
        invoice_payments_empty: "No payments for this invoice.",
        user_invoice_items_empty: "No items",
        user_invoice_payments_th_date: "Date",
        user_invoice_payments_th_method: "Method",
        user_invoice_payments_th_amount: "Amount",
        user_invoice_payments_th_comment: "Comment",
        user_invoice_payment_method_advance: "Advance",
        user_invoice_payments_summary: "Paid: {paid} · Remaining: {remaining} of {total}",
        user_invoice_pay_btn: "Pay",
        user_invoice_items_title: "Description",
        user_invoice_items_th_description: "Description",
        user_invoice_items_th_consumed: "Consumed",
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
        user_resident_tag: "Resident",
        user_resident_info: "Resident Information",
        user_to_pay_month: "Amount due this month",
        user_for_month: "This month",
        user_paid_short: "Paid",
        user_debt: "Debt by bills",
        user_advance: "Advance",
        user_to_pay_now: "Due now",
        user_btn_details: "Details",
        user_btn_my_bills: "My bills",
        user_btn_report_payment: "Pay unpaid bills",
        user_btn_pay_from_advance: "Pay from advance",
        user_btn_pay_month: "Pay for month",
        user_btn_pay_all: "Pay all",
        user_balance: "Balance",
        user_unpaid_bills: "Unpaid bills",
        user_unpaid_count: "unpaid",
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
        user_quick_documents: "News",
        user_quick_view_all: "View all",
        user_news_title: "News & announcements",
        user_no_news: "No news available",
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
        
        // Payment page
        payment_select_method: "Select payment method",
        payment_add_new_card: "Add new",
        payment_card_payment: "Card payment",
        payment_amount_label: "Amount to pay",
        payment_card_number: "Card number",
        payment_card_number_placeholder: "2324 5566 6677 7898",
        payment_card_name: "Name on card",
        payment_card_name_placeholder: "First Last",
        payment_card_expiry: "Expiry date",
        payment_card_expiry_placeholder: "11/25",
        payment_card_cvv: "CVV",
        payment_card_cvv_placeholder: "123",
        payment_save_card: "Save card",
        payment_pay_button: "Pay",
        payment_details_title: "Payment details",
        payment_order_subtitle: "Invoice payment",
        payment_type_label: "Payment type",
        payment_resident_label: "Resident",
        payment_period_label: "Period",
        payment_invoice_label: "Invoice",
        payment_total_label: "Total",
        payment_custom_amount: "Enter a different amount to pay",
        payment_custom_amount_label: "Amount to pay",
        payment_topup_advance_btn: "Top up advance",
        payment_cancel_topup_btn: "Cancel advance top-up",
        payment_topup_advance_label: "Advance top-up",
        payment_time_expired: "Payment time expired. Data cleared, please start over.",
        payment_time_remaining: "Time to pay",
        payment_all_debt: "Pay all debt",
        payment_current_month: "Payment for current month",
        payment_full_debt: "Full debt repayment",
        payment_month_bills: "Payment of current month bills",
        payment_invoice_payment: "Invoice payment",
        payment_multiple_invoices: "Multiple invoices",
        payment_bank_label: "Bank",
        payment_card_holder_name: "Card holder name",
        payment_expiry_date: "Expiry date",
        payment_authorized_signature: "Authorized Signature",
        payment_card_property: "This card is property of the issuer.",
        payment_advance_balance: "Advance Balance",
        payment_resident_name: "Resident Name",
        payment_valid_thru: "Valid Thru",
        payment_resident_pass: "RESIDENT PASS",
        
        // Payment comments
        payment_comment_new_card: "Payment with new card ****{last4}",
        payment_comment_advance: "Deduction from Royal Park Pass advance",
        payment_comment_saved_card: "Payment with {brand} {suffix} card",
        payment_comment_online: "Online payment",

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
        
        // Pagination
        pagination_page: "Page",
        pagination_of: "of",
        pagination_total: "total",
        pagination_on: "On",
        pagination_per_page: "page:",
        
        // Additional labels
        user_personal_account: "Personal Account",
        user_due_date_prefix: "Due date:",
        
        // Months
        month_january: "January",
        month_february: "February",
        month_march: "March",
        month_april: "April",
        month_may: "May",
        month_june: "June",
        month_july: "July",
        month_august: "August",
        month_september: "September",
        month_october: "October",
        month_november: "November",
        month_december: "December",
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
            <button class="language-btn" data-lang="az" title="Azərbaycan">
                <span class="lang-code">AZ</span>
            </button>
            <button class="language-btn" data-lang="en" title="English">
                <span class="lang-code">EN</span>
            </button>
            <button class="language-btn" data-lang="ru" title="Русский">
                <span class="lang-code">RU</span>
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
        
        // Update file status if no file is selected
        const fileStatus = container.querySelector('#accountFileStatus');
        if (fileStatus && !fileStatus.classList.contains('has-file')) {
            const noFileKey = fileStatus.getAttribute('data-i18n');
            if (noFileKey) {
                fileStatus.textContent = this.translate(noFileKey, lang);
            }
        }
        
        // Translate titles
            container.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
                if (key) {
            element.title = this.translate(key, lang);
                }
            });
        
        // Update resident due date elements (dynamically generated)
        container.querySelectorAll('.resident-due-date').forEach(element => {
            const dueDateStr = element.dataset.residentDueDate;
            const dueState = element.dataset.residentDueState || '';
            if (dueDateStr) {
                const dueDate = new Date(dueDateStr);
                const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
                const formattedDate = dueDate.toLocaleDateString(locale, { 
                    day: '2-digit', 
                    month: '2-digit', 
                    year: 'numeric' 
                });
                const dueDatePrefix = this.translate('user_due_date_prefix', lang);
                element.textContent = `${dueDatePrefix} ${formattedDate}`;
                
                // Reapply styling based on due_state
                element.className = 'resident-due-date';
                if (dueState === 'over') {
                    element.classList.add('due-over');
                } else if (dueState === 'soon') {
                    element.classList.add('due-soon');
                } else if (dueState === 'ok') {
                    element.classList.add('due-ok');
                }
            }
        });
        
        // Update bill items (latest bills section)
        container.querySelectorAll('.bill-item').forEach(billItem => {
            const billDate = billItem.querySelector('.bill-date');
            const billTitle = billItem.querySelector('.bill-title');
            const badge = billItem.querySelector('.badge');
            
            if (billDate && billDate.dataset.periodMonth && billDate.dataset.periodYear) {
                // Update month name
                const monthKeys = [
                    'month_january', 'month_february', 'month_march', 'month_april',
                    'month_may', 'month_june', 'month_july', 'month_august',
                    'month_september', 'month_october', 'month_november', 'month_december'
                ];
                const monthKey = monthKeys[parseInt(billDate.dataset.periodMonth) - 1];
                let monthName = this.translate(monthKey, lang);
                // If translate returns the key itself, use fallback
                if (monthName === monthKey) {
                    const fallbackMonths = lang === 'az' 
                        ? ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'İyun', 'İyul', 'Avqust', 'Sentyabr', 'Oktyabr', 'Noyabr', 'Dekabr']
                        : lang === 'en'
                        ? ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        : ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
                    monthName = fallbackMonths[parseInt(billDate.dataset.periodMonth) - 1];
                }
                billDate.textContent = `${monthName} ${billDate.dataset.periodYear}`;
            }
            
            if (billTitle && billTitle.dataset.invoiceNumber) {
                // Update invoice prefix
                const invoicePrefixKey = this.translate('user_invoice_title_prefix', lang);
                const invoicePrefix = invoicePrefixKey.replace(':', ' #');
                billTitle.textContent = `${invoicePrefix}${billTitle.dataset.invoiceNumber}`;
            }
            
            if (badge && badge.dataset.isPaid !== undefined) {
                // Update badge text
                const isPaid = badge.dataset.isPaid === 'true';
                badge.textContent = isPaid 
                    ? this.translate('status_paid', lang)
                    : this.translate('user_to_pay_status', lang);
            }
        });
        
        // Update unpaid count in quick actions
        const actionUnpaidEl = container.querySelector('#actionUnpaidCount');
        if (actionUnpaidEl && actionUnpaidEl.dataset.unpaidCount !== undefined) {
            const unpaidCount = actionUnpaidEl.dataset.unpaidCount;
            const unpaidText = this.translate('user_unpaid_count', lang);
            actionUnpaidEl.textContent = `${unpaidCount} ${unpaidText}`;
        }
        
        // Update bill paid/remaining labels in bills table
        container.querySelectorAll('.user-bill-paid').forEach(element => {
            const paidAmount = element.dataset.paidAmount;
            if (paidAmount !== undefined) {
                const lang = this.currentLanguage || localStorage.getItem('language') || 'ru';
                const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
                const paidFormatted = new Intl.NumberFormat(locale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(parseFloat(paidAmount));
                const paidLabel = this.translate('user_bills_paid_label', lang);
                element.textContent = paidLabel.replace('{amount}', paidFormatted);
            }
        });
        
        container.querySelectorAll('.user-bill-remaining').forEach(element => {
            const remainingAmount = element.dataset.remainingAmount;
            if (remainingAmount !== undefined) {
                const lang = this.currentLanguage || localStorage.getItem('language') || 'ru';
                const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
                const remainingFormatted = new Intl.NumberFormat(locale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(parseFloat(remainingAmount));
                const remainingLabel = this.translate('user_bills_remaining_label', lang);
                element.textContent = remainingLabel.replace('{amount}', remainingFormatted);
            }
        });
        
        // Update period text in bills table
        container.querySelectorAll('td[data-period-from][data-period-to]').forEach(element => {
            const from = element.dataset.periodFrom;
            const to = element.dataset.periodTo;
            if (from && to) {
                element.textContent = `${from} - ${to}`;
            }
        });

        container.querySelectorAll('td[data-period-month][data-period-year]').forEach(element => {
            const month = parseInt(element.dataset.periodMonth);
            const year = element.dataset.periodYear;
            if (month && year) {
                const monthKeys = [
                    'month_january', 'month_february', 'month_march', 'month_april',
                    'month_may', 'month_june', 'month_july', 'month_august',
                    'month_september', 'month_october', 'month_november', 'month_december'
                ];
                const monthName = this.translate(monthKeys[month - 1], lang);
                element.textContent = `${monthName} ${year}`;
            }
        });
        
        // Update due date in bills table
        container.querySelectorAll('td[data-due-date]').forEach(element => {
            const dueDateStr = element.dataset.dueDate;
            if (dueDateStr) {
                const dueDate = new Date(dueDateStr);
                const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
                element.textContent = dueDate.toLocaleDateString(locale);
            } else {
                element.textContent = '—';
            }
        });
        
        // Update status text in bills table
        container.querySelectorAll('.user-bill-status[data-status]').forEach(element => {
            const status = element.dataset.status;
            if (status) {
                const statusKey = `status_${status.toLowerCase()}`;
                const translated = this.translate(statusKey, lang);
                if (translated && translated !== statusKey) {
                    element.textContent = translated;
                }
            }
        });
        
        // Update status labels in filter dropdown
        container.querySelectorAll('span[data-status-value]').forEach(element => {
            const statusValue = element.dataset.statusValue;
            if (statusValue) {
                const statusKey = `status_${statusValue.toLowerCase()}`;
                const translated = this.translate(statusKey, lang);
                if (translated && translated !== statusKey) {
                    element.textContent = translated;
                }
            }
        });
        
        // Update buttons with data-i18n attribute
        container.querySelectorAll('button[data-i18n]').forEach(button => {
            const i18nKey = button.getAttribute('data-i18n');
            if (i18nKey) {
                const translated = this.translate(i18nKey, lang);
                if (translated && translated !== i18nKey) {
                    button.textContent = translated;
                }
            }
        });
        
        // Update appeal status badges
        container.querySelectorAll('.user-appeal-badge[data-appeal-status]').forEach(badge => {
            const status = badge.dataset.appealStatus;
            if (status === 'read') {
                badge.textContent = this.translate('user_appeal_status_read', lang);
            } else if (status === 'unread') {
                badge.textContent = this.translate('user_appeal_status_unread', lang);
            }
        });
        
        // Update appeal status in modal
        const modalStatus = container.querySelector('[data-appeal-status]');
        if (modalStatus && modalStatus.dataset.appealStatus) {
            const status = modalStatus.dataset.appealStatus;
            if (status === 'read') {
                modalStatus.textContent = this.translate('user_appeal_status_read', lang);
            } else if (status === 'unread') {
                modalStatus.textContent = this.translate('user_appeal_status_unread', lang);
            }
        }
        
        // Update pagination labels
        container.querySelectorAll('.pagination-info [data-i18n], .pagination-per-page [data-i18n]').forEach(el => {
            const i18nKey = el.getAttribute('data-i18n');
            if (i18nKey) {
                const translated = this.translate(i18nKey, lang);
                if (translated && translated !== i18nKey) {
                    el.textContent = translated;
                }
            }
        });
        
        // Update invoice period
        const invoicePeriodEl = container.querySelector('#invoicePeriod');
        if (invoicePeriodEl && invoicePeriodEl.dataset.periodMonth && invoicePeriodEl.dataset.periodYear) {
            const month = parseInt(invoicePeriodEl.dataset.periodMonth);
            const year = invoicePeriodEl.dataset.periodYear;
            const monthKeys = [
                'month_january', 'month_february', 'month_march', 'month_april',
                'month_may', 'month_june', 'month_july', 'month_august',
                'month_september', 'month_october', 'month_november', 'month_december'
            ];
            const monthName = this.translate(monthKeys[month - 1], lang);
            invoicePeriodEl.textContent = `${monthName} ${year}`;
        }
        
        // Update invoice due date
        const invoiceDueDateEl = container.querySelector('#invoiceDueDate');
        if (invoiceDueDateEl && invoiceDueDateEl.dataset.dueDate) {
            const dueDate = new Date(invoiceDueDateEl.dataset.dueDate);
            const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
            invoiceDueDateEl.textContent = dueDate.toLocaleDateString(locale);
        }
        
        // Update payments summary
        const paymentsSummaryEl = container.querySelector('#paymentsSummary');
        if (paymentsSummaryEl) {
            const summarySpan = paymentsSummaryEl.querySelector('span[data-paid-amount]');
            if (summarySpan) {
                const paidAmount = parseFloat(summarySpan.dataset.paidAmount || 0);
                const remainingAmount = parseFloat(summarySpan.dataset.remainingAmount || 0);
                const totalAmount = parseFloat(summarySpan.dataset.totalAmount || 0);
                const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
                const summaryTemplate = this.translate('user_invoice_payments_summary', lang);
                const paidFormatted = new Intl.NumberFormat(locale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(paidAmount);
                const remainingFormatted = new Intl.NumberFormat(locale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(remainingAmount);
                const totalFormatted = new Intl.NumberFormat(locale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(totalAmount);
                const summaryTextNew = summaryTemplate
                    .replace('{paid}', `<strong>${paidFormatted}</strong>`)
                    .replace('{remaining}', `<strong>${remainingFormatted}</strong>`)
                    .replace('{total}', `<strong>${totalFormatted}</strong>`);
                summarySpan.innerHTML = summaryTextNew;
            }
        }
        
        // Update empty payments message
        container.querySelectorAll('td[data-i18n-empty="invoice_payments_empty"]').forEach(element => {
            const emptyText = this.translate('invoice_payments_empty', lang);
            element.textContent = emptyText;
        });
        
        // Update payment comments in invoice view
        container.querySelectorAll('td[data-original-comment]').forEach(element => {
            const originalComment = element.dataset.originalComment;
            if (originalComment && originalComment !== '—') {
                // Используем глобальную функцию перевода, если она доступна
                if (window.translatePaymentComment && typeof window.translatePaymentComment === 'function') {
                    try {
                        const translated = window.translatePaymentComment(originalComment, lang);
                        if (translated) {
                            element.textContent = translated;
                        }
                    } catch (e) {
                        console.warn('Error translating payment comment:', e);
                    }
                }
            }
        });
        
        // Update invoice print page elements
        // Update invoice status in print page
        const invoiceStatusPrint = container.querySelector('#invoiceStatus[data-status]');
        if (invoiceStatusPrint && invoiceStatusPrint.dataset.status) {
            const statusKey = `status_${invoiceStatusPrint.dataset.status.toLowerCase()}`;
            invoiceStatusPrint.textContent = this.translate(statusKey, lang);
        }
        
        // Update generated date in print page
        const generatedDateEl = container.querySelector('#generatedDate');
        if (generatedDateEl) {
            const now = new Date();
            const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
            generatedDateEl.textContent = now.toLocaleString(locale);
        }
        
        // Update invoice payments summary in print page
        const invoicePaymentsSummaryEl = container.querySelector('#invoicePaymentsSummary');
        if (invoicePaymentsSummaryEl) {
            const summaryTemplate = this.translate('user_invoice_print_payments_summary', lang);
            // Пытаемся найти значения из текущего текста или используем 0
            const currentText = invoicePaymentsSummaryEl.textContent || '';
            const paidMatch = currentText.match(/[\d.]+/);
            const paidStr = paidMatch ? paidMatch[0] : '0.00';
            const remainingMatch = currentText.match(/[\d.]+/g);
            const remainingStr = remainingMatch && remainingMatch.length > 1 ? remainingMatch[1] : '0.00';
            const totalStr = remainingMatch && remainingMatch.length > 2 ? remainingMatch[2] : '0.00';
            
            const summaryText = summaryTemplate
                .replace('{paid}', `<strong>${paidStr}</strong>`)
                .replace('{remaining}', `<strong>${remainingStr}</strong>`)
                .replace('{total}', `<strong>${totalStr}</strong>`);
            invoicePaymentsSummaryEl.innerHTML = summaryText;
        }
        
        // Update invoice due date in print page (if not already set with data attribute)
        const invoiceDueDatePrint = container.querySelector('#invoiceDueDate');
        if (invoiceDueDatePrint && !invoiceDueDatePrint.dataset.dueDate) {
            const dueDateText = invoiceDueDatePrint.textContent;
            if (dueDateText && dueDateText !== '—') {
                try {
                    const date = new Date(dueDateText);
                    if (!isNaN(date.getTime())) {
                        const locale = lang === 'az' ? 'az-AZ' : lang === 'en' ? 'en-US' : 'ru-RU';
                        invoiceDueDatePrint.textContent = date.toLocaleDateString(locale);
                    }
                } catch (e) {
                    // Ignore errors
                }
            }
        }
        
        // Update invoice "Consumed" column (if present)
        container.querySelectorAll('td[data-consumed-qty]').forEach(element => {
            const qty = element.dataset.consumedQty;
            const unitKey = element.dataset.consumedUnitKey;
            if (qty) {
                const unit = unitKey ? this.translate(unitKey, lang) : '';
                element.textContent = `${qty}${unit ? ' ' + unit : ''}`.trim();
            } else {
                element.textContent = '—';
            }
        });

        // Update invoice line descriptions
        container.querySelectorAll('td[data-original-description]').forEach(element => {
            const serviceKey = element.dataset.serviceKey;
            if (serviceKey) {
                // New invoice table format: translate only service name (no qty/unit here)
                element.textContent = this.translate(serviceKey, lang);
                return;
            }

            // Legacy fallback (older templates): keep old behavior
            const originalDescription = element.dataset.originalDescription;
            if (originalDescription) {
                // Stable tariff lines: "Стабильный тариф (Электричество)" / "(Газ)" etc.
                const stableMatch = originalDescription.match(/^Стабильный\s+тариф\s*\(([^)]+)\)\s*$/i);
                if (stableMatch) {
                    const serviceRu = (stableMatch[1] || '').trim().toLowerCase();
                    let svcKey = '';
                    if (serviceRu.includes('электр')) svcKey = 'meter_electricity';
                    else if (serviceRu.includes('газ')) svcKey = 'meter_gas';
                    else if (serviceRu.includes('вода')) svcKey = 'meter_cold_water';
                    else if (serviceRu.includes('канализац')) svcKey = 'meter_sewerage';

                    const stableLabel = this.translate('stable_tariff', lang);
                    const svcLabel = svcKey ? this.translate(svcKey, lang) : stableMatch[1].trim();
                    element.textContent = `${stableLabel} (${svcLabel})`;
                    return;
                }

                const patterns = [
                    {
                        regex: /^Электричество\s+([\d.]+)\s*кВт·ч$/i,
                        serviceKey: 'meter_electricity',
                        unitKey: 'user_unit_kwh',
                        format: (amount, service, unit) => `${service} ${amount} ${unit}`
                    },
                    {
                        regex: /^Вода\s+([\d.]+)\s*м³$/i,
                        serviceKey: 'meter_cold_water',
                        unitKey: 'user_unit_m3',
                        format: (amount, service, unit, lang) => {
                            let waterText = 'Вода';
                            if (lang === 'az') waterText = 'Su';
                            else if (lang === 'en') waterText = 'Water';
                            return `${waterText} ${amount} ${unit}`;
                        }
                    },
                    {
                        regex: /^Газ\s+([\d.]+)\s*м³$/i,
                        serviceKey: 'meter_gas',
                        unitKey: 'user_unit_m3',
                        format: (amount, service, unit) => `${service} ${amount} ${unit}`
                    },
                    {
                        regex: /^Горячая\s+вода\s+([\d.]+)\s*м³$/i,
                        serviceKey: 'meter_hot_water',
                        unitKey: 'user_unit_m3',
                        format: (amount, service, unit) => `${service} ${amount} ${unit}`
                    }
                ];

                let translated = originalDescription;
                for (const pattern of patterns) {
                    const match = originalDescription.match(pattern.regex);
                    if (match) {
                        const amount = match[1];
                        const service = this.translate(pattern.serviceKey, lang);
                        const unit = this.translate(pattern.unitKey, lang);
                        translated = pattern.format(amount, service, unit);
                        break;
                    }
                }
                element.textContent = translated;
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

