import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, SessionLocal
from .models import User, RoleEnum
from .security import hash_password
from .routers import auth_routes, dashboard, users, blocks, tariffs, residents, readings, tenants, resident_portal, invoices, payments, notifications, api_users, api_blocks, api_tariffs, api_residents, api_readings, api_tenants, api_invoices, api_payments, api_notifications, api_dashboard, api_logs, api_qr, api_payment
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles
import os



def init_db():
    Base.metadata.create_all(bind=engine)
    run_bootstrap_schema()

    db: Session = SessionLocal()
    try:
        root = db.query(User).filter(User.username == settings.ROOT_USERNAME).first()
        if not root:
            root = User(
                username=settings.ROOT_USERNAME,
                password_hash=hash_password(settings.ROOT_PASSWORD),
                role=RoleEnum.ROOT,
                require_password_change=False,
                temp_password_plain=None,
            )
            db.add(root)
            db.commit()
    finally:
        db.close()

def run_bootstrap_schema():
    """
    Мягкие DDL: новые поля и таблицы — безопасно на каждом старте.
    """
    ddl_statements = [
        # (если раньше ещё не добавили эти поля, оставь — IF NOT EXISTS защитит)
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name varchar(200);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone     varchar(50);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email     varchar(120);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS comment   varchar(500);",
        # НОВОЕ: путь к аватару
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_path varchar(255);",
        # M2M таблица (если не создана)
        """
        CREATE TABLE IF NOT EXISTS user_residents (
          user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          resident_id INTEGER NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
          PRIMARY KEY (user_id, resident_id)
        );
        """
        # ... (твои предыдущие DDL тут могут быть)
        """
           CREATE TABLE IF NOT EXISTS resident_services (
             id SERIAL PRIMARY KEY,
             resident_id INTEGER NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
             service_type VARCHAR(16) NOT NULL,
             amount NUMERIC(18,2) NOT NULL DEFAULT 0,
             vat_percent INTEGER NOT NULL DEFAULT 0,
             is_active BOOLEAN NOT NULL DEFAULT TRUE,
             created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
             created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL
           );
           """
        "ALTER TABLE invoice_lines ALTER COLUMN meter_reading_id DROP NOT NULL;",
        "ALTER TABLE tariff_steps ADD COLUMN IF NOT EXISTS from_date DATE;",
        "ALTER TABLE tariff_steps ADD COLUMN IF NOT EXISTS to_date DATE;",
        "ALTER TABLE tariff_steps ALTER COLUMN from_value DROP NOT NULL;",
        "ALTER TABLE tariff_steps ALTER COLUMN to_value DROP NOT NULL;",
        # QR Tokens table
        """
        CREATE TABLE IF NOT EXISTS qr_tokens (
          id SERIAL PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          token VARCHAR(128) NOT NULL UNIQUE,
          is_used BOOLEAN NOT NULL DEFAULT FALSE,
          created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
          used_at TIMESTAMP WITHOUT TIME ZONE NULL
        );
        """,

    ]
    from .database import engine
    with engine.begin() as conn:
        for sql in ddl_statements:
            conn.exec_driver_sql(sql)

    # Гарантируем папку для аватаров
    os.makedirs("uploads/avatars", exist_ok=True)



def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Admin (Dark)")
    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY, session_cookie=settings.COOKIE_NAME)

    # Разрешаем запросы с фронта на 3000 порту
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3000/", "http://127.0.0.1:3000/"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    app.include_router(auth_routes.router)
    app.include_router(dashboard.router)
    app.include_router(users.router)
    app.include_router(api_users.router)
    app.include_router(api_blocks.router)
    app.include_router(api_tariffs.router)
    app.include_router(api_residents.router)
    app.include_router(api_readings.router)
    app.include_router(api_tenants.router)
    app.include_router(api_invoices.router)
    app.include_router(api_payments.router)
    app.include_router(api_notifications.router)
    app.include_router(api_dashboard.router)
    app.include_router(api_logs.router)
    app.include_router(api_qr.router)
    app.include_router(api_payment.router)
    app.include_router(blocks.router)
    app.include_router(tariffs.router)
    app.include_router(residents.router)
    app.include_router(readings.router)
    app.include_router(tenants.router)
    app.include_router(resident_portal.router)
    app.include_router(invoices.router)
    app.include_router(payments.router)
    app.include_router(notifications.router)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/favicon.ico")
    def favicon():
        return RedirectResponse(url="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/favicon.ico")

    return app


init_db()
app = create_app()
