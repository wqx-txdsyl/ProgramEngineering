import jwt
from fastapi import Depends, HTTPException
from fastapi.security import(
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlmodel import Session

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.database import get_session
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
        credentials:HTTPAuthorizationCredentials | None = Depends(
            bearer_scheme
            ),
            session:Session = Depends(get_session),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Please Login to Continue",
        headers={"WWW-Authenticate":"Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require":["sub", "exp"]},
        )

        user_id = int(payload["sub"])

    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized

    user = session.get(User, user_id)

    if user is None:
        raise unauthorized

    return user

def require_teacher(
        current_user:User = Depends(get_current_user),
) -> User:
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    return current_user

def require_student(
        current_user:User = Depends(get_current_user),
) -> User:
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    return current_user