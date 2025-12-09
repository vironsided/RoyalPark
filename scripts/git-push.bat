@echo off
REM Скрипт для безопасного пуша изменений
REM Использование: git-push.bat [branch_name] [commit_message]

setlocal

if "%1"=="" (
    echo Использование: git-push.bat [branch_name] [commit_message]
    echo Пример: git-push.bat feature/user "Update user dashboard"
    exit /b 1
)

set BRANCH=%1
set MESSAGE=%2

if "%MESSAGE%"=="" (
    set /p MESSAGE="Введите сообщение коммита: "
)

echo ========================================
echo Пуш изменений в ветку: %BRANCH%
echo ========================================
echo.

REM Проверяем текущую ветку
git branch --show-current > temp_current_branch.txt
set /p CURRENT_BRANCH=<temp_current_branch.txt
del temp_current_branch.txt

if not "%CURRENT_BRANCH%"=="%BRANCH%" (
    echo [1/4] Переключение на ветку %BRANCH%...
    git checkout %BRANCH%
    if errorlevel 1 (
        echo ОШИБКА: Не удалось переключиться на ветку %BRANCH%
        exit /b 1
    )
)

REM Обновляем перед пушем
echo [2/4] Обновление перед пушем...
git pull origin %BRANCH%
if errorlevel 1 (
    echo ВНИМАНИЕ: Ветка %BRANCH% еще не существует на origin (это нормально)
)

REM Добавляем все изменения
echo [3/4] Добавление изменений...
git add .

REM Коммитим
echo [4/4] Создание коммита...
git commit -m "%MESSAGE%"
if errorlevel 1 (
    echo ВНИМАНИЕ: Нет изменений для коммита или коммит отменен
)

REM Пушим
echo.
echo Отправка в origin/%BRANCH%...
git push origin %BRANCH%
if errorlevel 1 (
    echo ОШИБКА: Не удалось отправить изменения
    echo Попробуйте: git push -u origin %BRANCH%
    exit /b 1
)

echo.
echo ========================================
echo Успешно! Изменения отправлены в %BRANCH%
echo ========================================
echo.
echo Следующий шаг: Создайте Pull Request на GitHub
echo from: %BRANCH% -> into: develop

endlocal

