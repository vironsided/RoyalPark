// 🚀 SPA Router for RoyalPark Admin Panel
// Single Page Application роутер

class SPARouter {
    constructor() {
        this.routes = {
            // Главное
            '/': '/admin/content/dashboard.html',
            '/dashboard': '/admin/content/dashboard.html',
            '/analytics': '/admin/content/analytics.html',
            '/reports': '/admin/content/reports.html',
            
            // Управление
            '/blocks': '/admin/content/blocks.html',
            '/tariffs': '/admin/content/tariffs.html',
            '/residents': '/admin/content/residents.html',
            '/tenants': '/admin/content/tenants.html',
            '/readings': '/admin/content/readings.html',
            
            // Финансы
            '/payments': '/admin/content/payments.html',
            '/invoices': '/admin/content/invoices.html',
            '/debts': '/admin/content/debts.html',
            '/appeals-table': '/admin/content/appeals-table.html',
            '/invoice-view': '/admin/content/invoice-view.html',
            
            // Обслуживание
            '/repair-requests': '/admin/content/repair-requests.html',
            '/inspections': '/admin/content/inspections.html',
            '/staff': '/admin/content/staff.html',
            
            // Система
            '/settings': '/admin/content/settings.html',
            '/logs': '/admin/content/logs.html',
            '/backup': '/admin/content/backup.html',
            
            // Недвижимость
            '/buildings': '/admin/content/buildings.html',
            '/apartments': '/admin/content/apartments.html',
            '/users': '/admin/content/users.html',
            '/meters': '/admin/content/meters.html'
        };
        
        // Маппинг роутов к заголовкам и breadcrumbs
        this.pageInfo = {
            // Главное
            '/dashboard': {
                title: 'Панель управления',
                breadcrumb: ['Главная', 'Панель управления'],
                section: 'Главное'
            },
            '/analytics': {
                title: 'Аналитика',
                breadcrumb: ['Главная', 'Аналитика'],
                section: 'Главное'
            },
            '/reports': {
                title: 'Отчеты',
                breadcrumb: ['Главная', 'Отчеты'],
                section: 'Главное'
            },
            
            // Управление
            '/blocks': {
                title: 'Блоки',
                breadcrumb: ['Управление', 'Блоки'],
                section: 'Управление'
            },
            '/tariffs': {
                title: 'Тарифы',
                breadcrumb: ['Управление', 'Тарифы'],
                section: 'Управление'
            },
            '/residents': {
                title: 'Резиденты',
                breadcrumb: ['Управление', 'Резиденты'],
                section: 'Управление'
            },
            '/tenants': {
                title: 'Жители',
                breadcrumb: ['Управление', 'Жители'],
                section: 'Управление'
            },
            '/readings': {
                title: 'Показатели',
                breadcrumb: ['Управление', 'Показатели'],
                section: 'Управление'
            },
            '/users': {
                title: 'Пользователи',
                breadcrumb: ['Управление', 'Пользователи'],
                section: 'Управление'
            },
            
            // Финансы
            '/payments': {
                title: 'Платежи',
                breadcrumb: ['Финансы', 'Платежи'],
                section: 'Финансы'
            },
            '/invoices': {
                title: 'Счета',
                breadcrumb: ['Финансы', 'Счета'],
                section: 'Финансы'
            },
            '/debts': {
                title: 'Обращения',
                breadcrumb: ['Финансы', 'Обращения'],
                section: 'Финансы'
            },
            '/appeals-table': {
                title: 'Обращения жителей',
                breadcrumb: ['Финансы', 'Обращения', 'Таблица'],
                section: 'Финансы'
            },
            '/invoice-view': {
                title: 'Invoice view',
                breadcrumb: ['Финансы', 'Счета', 'Invoice view'],
                section: 'Финансы'
            },
            
            // Обслуживание
            '/repair-requests': {
                title: 'Заявки на ремонт',
                breadcrumb: ['Обслуживание', 'Заявки на ремонт'],
                section: 'Обслуживание'
            },
            '/inspections': {
                title: 'Проверки',
                breadcrumb: ['Обслуживание', 'Проверки'],
                section: 'Обслуживание'
            },
            '/staff': {
                title: 'Персонал',
                breadcrumb: ['Обслуживание', 'Персонал'],
                section: 'Обслуживание'
            },
            
            // Система
            '/settings': {
                title: 'Настройки',
                breadcrumb: ['Система', 'Настройки'],
                section: 'Система'
            },
            '/logs': {
                title: 'Логи',
                breadcrumb: ['Система', 'Логи'],
                section: 'Система'
            },
            '/backup': {
                title: 'Резервное копирование',
                breadcrumb: ['Система', 'Резервное копирование'],
                section: 'Система'
            }
        };
        
        this.contentContainer = null;
        this.currentRoute = null;
        this.isLoading = false;
    }
    
    normalizeRoute(route) {
        if (!route) return '/dashboard';
        const [baseRoute] = route.split('?');
        if (!baseRoute || baseRoute === '/') return '/dashboard';
        return baseRoute;
    }
    
    init() {
        this.contentContainer = document.getElementById('spa-content');
        
        if (!this.contentContainer) {
            console.error('SPA content container not found!');
            return;
        }
        
        // Обрабатываем клики на ссылки меню
        this.setupNavigationListeners();
        
        // Обрабатываем кнопки "назад" и "вперед"
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.route) {
                this.loadContent(e.state.route, false);
            }
        });
        
        // Загружаем начальную страницу
        const initialRoute = this.getRouteFromHash();
        this.navigate(initialRoute || '/dashboard');
    }
    
    setupNavigationListeners() {
        // Находим все ссылки в меню
        document.querySelectorAll('.nav-item').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Используем data-route если есть, иначе href
                const route = link.getAttribute('data-route') || link.getAttribute('href');
                
                this.navigate(route);
            });
        });
    }
    
    extractRoute(href) {
        // Извлекаем роут из href
        // Поддерживаем разные форматы:
        // /blocks -> /blocks
        // /admin/blocks -> /blocks
        // /admin/blocks.html -> /blocks
        if (!href) return '/dashboard';
        
        let route = href;
        
        // Убираем /admin/ если есть
        if (route.includes('/admin/')) {
            route = route.replace('/admin/', '/');
        }
        
        // Убираем .html если есть
        route = route.replace('.html', '');
        
        // Если осталось только '/' или '/index', возвращаем /dashboard
        if (route === '/' || route === '/index') {
            return '/dashboard';
        }
        
        return route;
    }
    
    getRouteFromHash() {
        const hash = window.location.hash.slice(1); // Убираем #
        return hash || '/';
    }
    
    navigate(route) {
        if (this.isLoading) return;
        
        // Обновляем URL
        window.location.hash = route;
        
        // Обновляем активный пункт меню
        this.updateActiveMenuItem(route);
        
        // Загружаем контент
        this.loadContent(route, true);
    }
    
    updateActiveMenuItem(route) {
        const baseRoute = this.normalizeRoute(route);
        // Убираем active со всех пунктов
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Добавляем active на текущий пункт
        document.querySelectorAll('.nav-item').forEach(item => {
            const href = item.getAttribute('href');
            const itemRoute = this.extractRoute(href);
            
            if (itemRoute === baseRoute) {
                item.classList.add('active');
            }
        });
    }
    
    async loadContent(route, updateHistory = true) {
        if (this.isLoading) return;
        
        const baseRoute = this.normalizeRoute(route);
        const contentPath = this.routes[baseRoute] || this.routes['/dashboard'];
        
        try {
            this.isLoading = true;
            this.showLoadingState();
            
            // Загружаем контент
            const response = await fetch(contentPath);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const html = await response.text();
            
            // Вставляем контент
            this.contentContainer.innerHTML = html;
            
            // Hide any plan tooltip from blocks page when navigating away
            const planTooltip = document.getElementById('planTooltip');
            if (planTooltip) {
                planTooltip.classList.add('hidden');
                planTooltip.style.display = 'none';
            }
            
            // Also call global hide function if it exists
            if (window.hidePlanTooltip) {
                window.hidePlanTooltip();
            }
            
            // Обновляем заголовок и breadcrumb
            this.updatePageTitle(baseRoute);
            
            // Обновляем историю браузера
            if (updateHistory) {
                history.pushState({ route }, '', `#${route}`);
            }
            
            this.currentRoute = route;
            
            // Инициализируем скрипты на новой странице
            this.initializePageScripts();
            
            // Применяем переводы после небольшой задержки, чтобы контент успел отрендериться
            setTimeout(() => {
                if (window.reapplyAutoTranslations) {
                    window.reapplyAutoTranslations();
                }
                if (window.i18n) {
                    const savedLang = localStorage.getItem('language') || window.i18n.currentLanguage || 'ru';
                    window.i18n.applyLanguage(savedLang);
                }
            }, 50);
            
            // Скроллим наверх
            this.contentContainer.scrollTop = 0;
            
        } catch (error) {
            console.error('Error loading content:', error);
            this.showErrorState(error);
        } finally {
            this.isLoading = false;
        }
    }
    
    showLoadingState() {
        this.contentContainer.innerHTML = `
            <div class="loading-state" style="display: flex; align-items: center; justify-content: center; min-height: 400px;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
            </div>
        `;
    }
    
    showErrorState(error) {
        this.contentContainer.innerHTML = `
            <div class="error-state" style="padding: 40px; text-align: center;">
                <div class="alert alert-danger">
                    <h4>❌ Ошибка загрузки</h4>
                    <p>${error.message}</p>
                    <button class="btn btn-primary mt-3" onclick="location.reload()">
                        Перезагрузить страницу
                    </button>
                </div>
            </div>
        `;
    }
    
    updatePageTitle(route) {
        const pageInfo = this.pageInfo[route] || this.pageInfo['/dashboard'];
        const titleContainer = document.getElementById('page-title-container');
        
        if (!titleContainer) return;
        
        // Обновляем заголовок
        const h1 = titleContainer.querySelector('h1');
        if (h1) {
            h1.textContent = pageInfo.title;
        }
        
        // Обновляем breadcrumb
        const breadcrumbContainer = titleContainer.querySelector('.page-breadcrumb');
        if (breadcrumbContainer) {
            let breadcrumbHtml = '';
            pageInfo.breadcrumb.forEach((crumb, index) => {
                if (index > 0) {
                    breadcrumbHtml += '<span>›</span>';
                }
                
                const iconHtml = index === 0 ? `
                    <svg width="14" height="14" fill="currentColor" style="margin-right: 0.25rem; vertical-align: middle;">
                        <use href="/images/icons.svg#icon-apartments"></use>
                    </svg>
                ` : '';
                
                breadcrumbHtml += `
                    <span class="breadcrumb-item">
                        ${iconHtml}
                        ${crumb}
                    </span>
                `;
            });
            
            breadcrumbContainer.innerHTML = breadcrumbHtml;
        }
        
        // Обновляем title страницы
        document.title = `${pageInfo.title} - RoyalPark Admin`;
    }
    
    initializePageScripts() {
        // Выполняем скрипты внутри загруженного контента
        const scripts = this.contentContainer.querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
        
        // Запускаем кастомное событие для инициализации компонентов
        window.dispatchEvent(new CustomEvent('spa:contentLoaded', {
            detail: { route: this.currentRoute }
        }));
    }
}

// Глобальный экспорт
window.SPARouter = SPARouter;

// Автоинициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('spa-content')) {
            window.spaRouter = new SPARouter();
            window.spaRouter.init();
        }
    });
} else {
    if (document.getElementById('spa-content')) {
        window.spaRouter = new SPARouter();
        window.spaRouter.init();
    }
}




