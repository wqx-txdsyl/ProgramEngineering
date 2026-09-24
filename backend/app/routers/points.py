from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.dependencies import require_student
from app.models import User
from app.schemas import PointBalanceRead, PointTransactionRead
from app.services.points import get_balance, list_transactions

router = APIRouter(
    prefix="/api/points",
    tags=["points"],
)

@router.get("/me", response_model=PointBalanceRead)
def get_my_points(
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    return PointBalanceRead(
        user_id=current_user.id,
        balance=get_balance(session, current_user.id),
    )

@router.get("/transactions", response_model=list[PointTransactionRead])
def list_my_transactions(
    offset:int = Query(default=0, ge=0),
    limit:int = Query(default=20, ge=1, le=100),
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    return list_transactions(
        session,
        current_user.id,
        offset=offset,
        limit=limit,
    )
