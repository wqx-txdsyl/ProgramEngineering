from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

from app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    JWT_ALGORITHM, 
    JWT_SECRET_KEY, 
)

password_hasher = PasswordHash.recommended()

DUMMY_PASSWORD_HASH = password_hasher.hash(
    "dummy-password-for-timing-check"
)

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(
        password:str,
        password_hash:str,
) -> bool:
    return password_hasher.verify(password, password_hash)

def create_access_token(user_id:int) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub":str(user_id),
        "exp":expire_at
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )