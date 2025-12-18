# 🔒 Настройка защиты веток на GitHub

## Рекомендуемые настройки защиты веток

Для безопасной совместной работы рекомендуется настроить защиту веток на GitHub:

### Для ветки `main`:

1. Перейдите: https://github.com/vironsided/RoyalPark/settings/branches
2. Нажмите "Add rule" для ветки `main`
3. Включите:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (минимум 1)
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings

### Для ветки `develop`:

1. Добавьте правило для ветки `develop`
2. Включите:
   - ✅ Require a pull request before merging
   - ✅ Require branches to be up to date before merging

### Для feature веток:

Защита не требуется, разработчики могут пушить напрямую.

---

## Как настроить:

1. Зайдите на GitHub: https://github.com/vironsided/RoyalPark/settings/branches
2. Нажмите "Add branch protection rule"
3. Введите имя ветки (например, `main` или `develop`)
4. Выберите нужные опции
5. Нажмите "Create"

---

**Важно:** Только владелец репозитория может настроить защиту веток.

