from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from sqlmodel import Session, select
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas import Register, UserRead
from app.models import User
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

def register_user(session:Session, register_data:Register) -> User:
    statement = select(User).where(
        User.username == register_data.username
    )

    existing_user = session.exec(statement).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Username has been registered"
        )

    user = User(
        username=register_data.username,
        password_hash=hash_password(register_data.password),
        role="student"
    )

    session.add(user)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()

        existing_user = session.exec(statement).first()
        if existing_user is not None:
            raise HTTPException(
                status_code=409,
                detail="Username has been registered"
            )

        raise

    session.refresh(user)
    return user