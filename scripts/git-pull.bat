@echo off
REM Скрипт для безопасного обновления ветки перед работой
REM Использование: git-pull.bat [branch_name]

setlocal

if "%1"=="" (
    echo Использование: git-pull.bat [branch_name]
    echo Пример: git-pull.bat feature/user
    exit /b 1
)

set BRANCH=%1

echo ========================================
echo Обновление ветки: %BRANCH%
echo ========================================
echo.

REM Переключаемся на нужную ветку
echo [1/3] Переключение на ветку %BRANCH%...
git checkout %BRANCH%
if errorlevel 1 (
    echo ОШИБКА: Не удалось переключиться на ветку %BRANCH%
    exit /b 1
)

REM Обновляем develop (если не develop)
if not "%BRANCH%"=="develop" (
    echo [2/3] Обновление develop...
    git checkout develop
    git pull origin develop
    git checkout %BRANCH%
)

REM Обновляем текущую ветку
echo [3/3] Обновление %BRANCH% из origin...
git pull origin %BRANCH%
if errorlevel 1 (
    echo ВНИМАНИЕ: Ветка %BRANCH% еще не существует на origin
    echo Это нормально для новых веток
)

echo.
echo ========================================
echo Готово! Ветка %BRANCH% обновлена
echo ========================================

endlocal

