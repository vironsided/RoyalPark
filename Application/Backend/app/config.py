from pydantic import BaseModel


class Settings(BaseModel):
    # Подключение к БД (из задачи):
    PG_HOST: str = "127.0.0.1"
    PG_PORT: int = 5432
    PG_USER: str = "postgres"
    PG_PASSWORD: str = "admin Ayaz"
    PG_DB: str = "fastApiAyaz"

    # Секреты/куки:
    SESSION_SECRET_KEY: str = "change-this-in-production"
    COOKIE_NAME: str = "session_id"

    # Root-учётка из ТЗ:
    ROOT_USERNAME: str = "root"
    ROOT_PASSWORD: str = "admin Ayaz"


settings = Settings()
