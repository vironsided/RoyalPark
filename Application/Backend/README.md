# FastAPI Admin (Dark)

## Подготовка БД
Создай БД `fastapi_admin` в PostgreSQL:
```sql
CREATE DATABASE fastapi_admin;
```

## Переменные окружения (.env)
Все конфигурации и секреты вынесены в `Backend/.env`.

1. Скопируй шаблон:
```bash
cp .env.example .env
```
2. Заполни `.env` своими значениями (БД, ROOT, AzeriCard, Firebase).

## Запуск (Windows / Linux)
```bash
python -m venv .venv
# Windows:
. .venv/Scripts/activate
# Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Открой http://127.0.0.1:8000/login

## Запуск через Docker
Из корня проекта `RoyalPark`:

```bash
docker compose up --build
```

После старта:
- Backend: http://127.0.0.1:8000/login
- Healthcheck: http://127.0.0.1:8000/healthz

Важно для Docker:
- Бэкенд подключается к БД по `PG_HOST=db` (имя сервиса в `docker-compose.yml`).
- Для локального запуска без Docker можно оставить `PG_HOST=127.0.0.1`.

Вход ROOT берётся из `.env`:
- `ROOT_USERNAME`
- `ROOT_PASSWORD`

## Политика ролей
- ROOT: полный доступ, может создавать/редактировать/удалять всех, видеть/сбрасывать временные пароли.
- ADMIN: может управлять только OPERATOR и RESIDENT. Не может редактировать/удалять ADMIN/ROOT.
- OPERATOR, RESIDENT: без прав управления пользователями.

## Особенности
- Для новых пользователей генерируется временный пароль (видно на странице пользователeй).
- При первом входе (или после сброса) — принудительная смена пароля.
- Для root смена не требуется по умолчанию.
