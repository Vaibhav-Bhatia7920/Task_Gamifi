import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")
load_dotenv(APP_DIR.parent / ".env")


def build_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    name = os.getenv("POSTGRES_DB")
    if user and password and name:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

    return "sqlite+aiosqlite:///./task_gamifi.db"


DATABASE_URL = build_database_url()
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
