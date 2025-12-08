# FastAPI Admin (Dark)

## Подготовка БД
Создай БД `fastapi_admin` в PostgreSQL:
```sql
CREATE DATABASE fastapi_admin;
```

## Настройки подключения
`app/config.py` уже содержит:
- Host: 127.0.0.1
- Port: 5432
- Login: postgres
- Pass: "admin Ayaz"

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

Вход ROOT:
- Логин: `root`
- Пароль: `admin Ayaz`

## Политика ролей
- ROOT: полный доступ, может создавать/редактировать/удалять всех, видеть/сбрасывать временные пароли.
- ADMIN: может управлять только OPERATOR и RESIDENT. Не может редактировать/удалять ADMIN/ROOT.
- OPERATOR, RESIDENT: без прав управления пользователями.

## Особенности
- Для новых пользователей генерируется временный пароль (видно на странице пользователeй).
- При первом входе (или после сброса) — принудительная смена пароля.
- Для root смена не требуется по умолчанию.
