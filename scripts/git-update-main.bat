@echo off
REM Скрипт для обновления ветки main из origin

echo ========================================
echo Обновление ветки main
echo ========================================
echo.

REM Проверяем что мы на main
git branch --show-current > temp_current_branch.txt
set /p CURRENT_BRANCH=<temp_current_branch.txt
del temp_current_branch.txt

if not "%CURRENT_BRANCH%"=="main" (
    echo Переключение на ветку main...
    git checkout main
)

echo [1/2] Получение изменений из origin...
git fetch origin

echo [2/2] Обновление main...
git pull origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo ВНИМАНИЕ: Возможны конфликты!
    echo ========================================
    echo Проверьте файлы с конфликтами и решите их вручную
    echo Затем выполните: git add . && git commit
) else (
    echo.
    echo ========================================
    echo Готово! Ветка main обновлена
    echo ========================================
)

