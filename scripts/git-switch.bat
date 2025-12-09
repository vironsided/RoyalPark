@echo off
REM Скрипт для переключения между ветками
REM Использование: git-switch.bat [branch_name]

setlocal

if "%1"=="" (
    echo Доступные ветки:
    git branch
    echo.
    echo Использование: git-switch.bat [branch_name]
    echo Примеры:
    echo   git-switch.bat feature/user
    echo   git-switch.bat feature/admin
    echo   git-switch.bat develop
    exit /b 1
)

set BRANCH=%1

echo ========================================
echo Переключение на ветку: %BRANCH%
echo ========================================
echo.

REM Сохраняем текущие изменения (stash)
echo [1/2] Сохранение незакоммиченных изменений...
git stash push -m "Auto-stash before switch to %BRANCH%"

REM Переключаемся
echo [2/2] Переключение на %BRANCH%...
git checkout %BRANCH%
if errorlevel 1 (
    echo ОШИБКА: Не удалось переключиться на ветку %BRANCH%
    echo Восстановление изменений...
    git stash pop
    exit /b 1
)

REM Восстанавливаем изменения
echo.
echo Восстановление изменений...
git stash pop

echo.
echo ========================================
echo Готово! Вы на ветке %BRANCH%
echo ========================================

endlocal

