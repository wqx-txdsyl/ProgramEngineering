import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "please reconfigure your JWT_SECRET_KEY"
    )

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60