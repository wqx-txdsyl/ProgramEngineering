from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoginRequest, TokenRead, UserRead, Register
from app.services.auth import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    verify_password,
    register_user
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)

@router.post("/login", response_model=TokenRead)
def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session),
):
    statement = select(User).where(User.username == login_data.username)
    user = session.exec(statement).first()

    password_hash = (
        user.password_hash 
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    password_is_valid = verify_password(
        login_data.password,
        password_hash,
    )

    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate":"Bearer"},
        )

    return TokenRead(
        access_token=create_access_token(user.id),
    )

@router.get("/me", response_model=UserRead)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.post("/register", response_model=UserRead, status_code=201)
def register_new(
    register_data: Register,
    session:Session = Depends(get_session)
):
    user = register_user(session=session, register_data=register_data)

    return user