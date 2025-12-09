(() => {
    class UserSPARouter {
        constructor() {
            this.routes = {
                dashboard: {
                    type: 'inline',
                    content: '',
                    bodyClass: ''
                },
                bills: {
                    type: 'remote',
                    path: '/user/pages/bills.html',
                    bodyClass: ''
                },
                report: {
                    type: 'remote',
                    path: '/user/pages/report-payment.html',
                    bodyClass: '',
                    parentNav: 'report'
                },
                resident: {
                    type: 'remote',
                    path: '/user/pages/resident-detail.html',
                    bodyClass: 'resident-detail-page',
                    parentNav: 'dashboard'
                },
                appeals: {
                    type: 'remote',
                    path: '/user/pages/appeals.html',
                    bodyClass: ''
                },
                invoice: {
                    type: 'remote',
                    path: '/user/pages/invoice-view.html',
                    bodyClass: '',
                    parentNav: 'bills'
                }
            };

            this.contentContainer = null;
            this.currentRoute = null;
            this.isLoading = false;
        }

        init() {
            this.contentContainer = document.getElementById('userSpaContent');
            if (!this.contentContainer) return;

            this.routes.dashboard.content = this.contentContainer.innerHTML;

            this.setupNavigationListeners();
            this.setupActionTargets();

            window.addEventListener('popstate', (event) => {
                const route = event.state?.route || this.getRouteFromLocation();
                this.navigate(route, false);
            });

            const initialRoute = this.getRouteFromLocation();
            this.navigate(initialRoute, false);
        }

        getRouteFromLocation() {
            const hash = window.location.hash.replace('#', '');
            if (hash && this.routes[hash]) {
                return hash;
            }
            return 'dashboard';
        }

        setupNavigationListeners() {
            document.querySelectorAll('.nav-item[data-user-route]').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const route = link.getAttribute('data-user-route');
                    this.navigate(route, true);
                });
            });
        }

        setupActionTargets() {
            document.addEventListener('click', (event) => {
                const target = event.target.closest('[data-user-route-target]');
                if (!target) return;
                event.preventDefault();
                const route = target.getAttribute('data-user-route-target');
                
                // If navigating to resident detail, store resident ID
                if (route === 'resident') {
                    // Try to get resident ID from button attribute or dashboard data
                    let residentId = target.getAttribute('data-resident-id');
                    
                    if (!residentId && window.dashboardData && window.dashboardData.residents && window.dashboardData.residents.length > 0) {
                        residentId = window.dashboardData.residents[0].id;
                    }
                    
                    if (residentId) {
                        sessionStorage.setItem('currentResidentId', residentId.toString());
                    } else {
                        console.warn('Resident ID not found, will try to load from backend');
                    }
                }
                
                // If navigating to invoice detail, store invoice ID
                if (route === 'invoice') {
                    const invoiceId = target.getAttribute('data-invoice-id');
                    if (invoiceId) {
                        sessionStorage.setItem('currentInvoiceId', invoiceId.toString());
                    }
                }
                
                this.navigate(route, true);
            });
        }

        navigate(route, updateHistory = true) {
            if (!route || !this.routes[route]) {
                route = 'dashboard';
            }

            if (this.currentRoute === route && !this.isLoading) {
                return;
            }

            if (updateHistory) {
                const url = route === 'dashboard'
                    ? window.location.pathname
                    : `${window.location.pathname}#${route}`;
                history.pushState({ route }, '', url);
            } else {
                history.replaceState({ route }, '', route === 'dashboard'
                    ? window.location.pathname
                    : `${window.location.pathname}#${route}`);
            }

            this.updateActiveMenu(route);
            this.applyBodyClass(route);

            const config = this.routes[route];
            if (config.type === 'inline') {
                this.contentContainer.innerHTML = config.content;
                this.afterContentRender(route);
                this.currentRoute = route;
                // Reload dashboard data if navigating to dashboard
                if (route === 'dashboard' && typeof loadDashboardData === 'function') {
                    setTimeout(() => {
                        loadDashboardData();
                    }, 100);
                }
                return;
            }

            this.loadRemoteRoute(route, config.path);
        }

        updateActiveMenu(route) {
            // Если у маршрута есть "родитель" для навигации (например, invoice -> bills),
            // подсвечиваем в меню именно его.
            const navRoute = this.routes[route]?.parentNav || route;

            document.querySelectorAll('.nav-item[data-user-route]').forEach(item => {
                item.classList.toggle('active', item.getAttribute('data-user-route') === navRoute);
            });
        }

        applyBodyClass(route) {
            Object.values(this.routes).forEach(cfg => {
                if (cfg.bodyClass) {
                    document.body.classList.remove(cfg.bodyClass);
                }
            });

            const current = this.routes[route];
            if (current?.bodyClass) {
                document.body.classList.add(current.bodyClass);
            }
        }

        async loadRemoteRoute(route, path) {
            if (this.isLoading) return;

            try {
                this.isLoading = true;
                this.showLoadingState();

                const response = await fetch(path, { cache: 'no-store' });
                if (!response.ok) {
                    throw new Error(`Ошибка загрузки ${response.status}`);
                }

                const html = await response.text();
                this.contentContainer.innerHTML = html;
                this.afterContentRender(route);
                this.currentRoute = route;
            } catch (error) {
                console.error(error);
                this.showErrorState(error);
            } finally {
                this.isLoading = false;
            }
        }

        showLoadingState() {
            this.contentContainer.innerHTML = `
                <div class="loading-state" style="display:flex;align-items:center;justify-content:center;min-height:400px;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Загрузка...</span>
                    </div>
                </div>
            `;
        }

        showErrorState(error) {
            this.contentContainer.innerHTML = `
                <div class="error-state" style="padding:32px;text-align:center;">
                    <div class="alert alert-danger">
                        <h4>Не удалось загрузить страницу</h4>
                        <p>${error.message}</p>
                        <button class="btn btn-primary mt-3" onclick="window.userSpaRouter.navigate('dashboard', true)">
                            Вернуться на главную
                        </button>
                    </div>
                </div>
            `;
        }

        afterContentRender(route) {
            this.executeInlineScripts();

            setTimeout(() => {
                if (window.reapplyAutoTranslations) {
                    window.reapplyAutoTranslations();
                }
                if (window.i18n) {
                    const savedLang = localStorage.getItem('language') || 'ru';
                    window.i18n.applyLanguage(savedLang);
                }
            }, 50);

            if (window.addCardAnimations) {
                window.addCardAnimations();
            }

            // Reload dashboard data if navigating to dashboard
            if (route === 'dashboard' && typeof loadDashboardData === 'function') {
                setTimeout(() => {
                    loadDashboardData();
                }, 150);
            }

            // Reload bills data if navigating to bills page
            if (route === 'bills') {
                // Reset any initialization flags if needed
                // The inline scripts will be executed automatically by executeInlineScripts()
                setTimeout(() => {
                    // Scripts in bills.html will auto-execute when loaded
                }, 100);
            }
        }

        executeInlineScripts() {
            const scripts = this.contentContainer.querySelectorAll('script');
            scripts.forEach(oldScript => {
                const newScript = document.createElement('script');
                Array.from(oldScript.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });
                newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        window.userSpaRouter = new UserSPARouter();
        window.userSpaRouter.init();
    });
})();

