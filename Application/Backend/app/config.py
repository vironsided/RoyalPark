import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Подключение к БД (из задачи):
    PG_HOST: str = os.getenv("PG_HOST", "127.0.0.1")
    PG_PORT: int = int(os.getenv("PG_PORT", "5432"))
    PG_USER: str = os.getenv("PG_USER", "postgres")
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "admin Ayaz")
    PG_DB: str = os.getenv("PG_DB", "fastApiAyaz")

    # Секреты/куки:
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "change-this-in-production")
    COOKIE_NAME: str = os.getenv("COOKIE_NAME", "session_id")

    # Root-учётка из ТЗ:
    ROOT_USERNAME: str = os.getenv("ROOT_USERNAME", "root")
    ROOT_PASSWORD: str = os.getenv("ROOT_PASSWORD", "admin Ayaz")
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

    # AzeriCard — general
    AZERICARD_GATEWAY_URL: str = os.getenv("AZERICARD_GATEWAY_URL", "https://testmpi.3dsecure.az/cgi-bin/cgi_link")
    AZERICARD_API_URL: str = os.getenv("AZERICARD_API_URL", "https://testmpi.3dsecure.az/cgi-bin/cgi_link")
    AZERICARD_MERCH_NAME: str = os.getenv("AZERICARD_MERCH_NAME", "Royal Park")
    AZERICARD_MERCH_URL: str = os.getenv("AZERICARD_MERCH_URL", "http://localhost:3000")
    AZERICARD_CALLBACK_URL: str = os.getenv("AZERICARD_CALLBACK_URL", "http://localhost:8000/api/azericard/callback")
    AZERICARD_SUCCESS_URL: str = os.getenv("AZERICARD_SUCCESS_URL", "http://localhost:8000/api/azericard/success")
    AZERICARD_FAIL_URL: str = os.getenv("AZERICARD_FAIL_URL", "http://localhost:8000/api/azericard/fail")
    AZERICARD_CURRENCY: str = os.getenv("AZERICARD_CURRENCY", "AZN")
    AZERICARD_LANG: str = os.getenv("AZERICARD_LANG", "en")

    # AzeriCard — legacy single-terminal (fallback)
    AZERICARD_TERMINAL_ID: str = os.getenv("AZERICARD_TERMINAL_ID", "TEST_TERMINAL_ID")
    AZERICARD_PRIVATE_KEY: str = os.getenv("AZERICARD_PRIVATE_KEY", "DUMMY_PRIVATE_KEY")
    AZERICARD_PUBLIC_KEY: str = os.getenv("AZERICARD_PUBLIC_KEY", "DUMMY_PUBLIC_KEY")

    # AzeriCard — per-category terminals (utility / maintenance / advance)
    AZERICARD_TERMINAL_UTILITY: str = os.getenv("AZERICARD_TERMINAL_UTILITY", "")
    AZERICARD_PRIVATE_KEY_UTILITY: str = os.getenv("AZERICARD_PRIVATE_KEY_UTILITY", "")
    AZERICARD_PUBLIC_KEY_UTILITY: str = os.getenv("AZERICARD_PUBLIC_KEY_UTILITY", "")

    AZERICARD_TERMINAL_MAINTENANCE: str = os.getenv("AZERICARD_TERMINAL_MAINTENANCE", "")
    AZERICARD_PRIVATE_KEY_MAINTENANCE: str = os.getenv("AZERICARD_PRIVATE_KEY_MAINTENANCE", "")
    AZERICARD_PUBLIC_KEY_MAINTENANCE: str = os.getenv("AZERICARD_PUBLIC_KEY_MAINTENANCE", "")

    AZERICARD_TERMINAL_ADVANCE: str = os.getenv("AZERICARD_TERMINAL_ADVANCE", "")
    AZERICARD_PRIVATE_KEY_ADVANCE: str = os.getenv("AZERICARD_PRIVATE_KEY_ADVANCE", "")
    AZERICARD_PUBLIC_KEY_ADVANCE: str = os.getenv("AZERICARD_PUBLIC_KEY_ADVANCE", "")


settings = Settings()
