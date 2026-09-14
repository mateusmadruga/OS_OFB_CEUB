import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "aula-dev-altere-em-producao")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'os_ofb.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
    WTF_CSRF_TIME_LIMIT = 3600
