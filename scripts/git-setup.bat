@echo off
REM Скрипт для первоначальной настройки Git workflow
REM Запускать один раз для настройки

setlocal

echo ========================================
echo Настройка Git Workflow для RoyalPark
echo ========================================
echo.

REM Проверяем подключение к origin
echo [1/4] Проверка подключения к origin...
git remote -v
if errorlevel 1 (
    echo ОШИБКА: Не найден remote origin
    exit /b 1
)

REM Обновляем main
echo [2/4] Обновление ветки main...
git checkout main
git pull origin main

REM Создаем develop если не существует
echo [3/4] Создание/обновление ветки develop...
git checkout -b develop 2>nul
git pull origin develop 2>nul || echo Ветка develop еще не существует на origin (это нормально)

REM Отправляем develop на origin
echo [4/4] Отправка develop на origin...
git push -u origin develop

echo.
echo ========================================
echo Настройка завершена!
echo ========================================
echo.
echo Следующие шаги:
echo 1. Создайте feature ветку: git checkout -b feature/your-name
echo 2. Или используйте готовые: feature/user или feature/admin
echo 3. Используйте скрипты из папки scripts/ для работы
echo.

endlocal

