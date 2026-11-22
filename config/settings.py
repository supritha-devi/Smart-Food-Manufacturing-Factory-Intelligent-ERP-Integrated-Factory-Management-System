import os


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 28800
    VOICE_STORAGE_PATH = os.getenv("VOICE_STORAGE_PATH")
    VOICE_RETENTION_DAYS = int(os.getenv("VOICE_RETENTION_DAYS", "365"))
    VOICE_STT_ENDPOINT = os.getenv("VOICE_STT_ENDPOINT")
    VOICE_STT_API_KEY = os.getenv("VOICE_STT_API_KEY")
    VOICE_STORAGE_PROVIDER = os.getenv("VOICE_STORAGE_PROVIDER", "local")


class TestingConfig(BaseConfig):
    TESTING = True
    SESSION_COOKIE_SECURE = False
