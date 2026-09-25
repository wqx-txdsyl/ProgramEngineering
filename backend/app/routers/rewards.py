from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user, require_student
from app.models import User
from app.schemas import RedeemRequest, RedemptionRead, RewardRead
from app.services.points import (
    cancel_redemption,
    list_redemptions,
    list_rewards,
    redeem_reward,
)

router = APIRouter(
    prefix="/api/rewards",
    tags=["rewards"],
)

@router.get("", response_model=list[RewardRead])
def list_available_rewards(
    offset:int = Query(default=0, ge=0),
    limit:int = Query(default=20, ge=1, le=100),
    session:Session = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    return list_rewards(session, offset=offset, limit=limit)

@router.post("/{reward_id}/redeem", response_model=RedemptionRead, status_code=201)
def redeem_one_reward(
    reward_id:int,
    redeem_data:RedeemRequest,
    response:Response,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    redemption, created = redeem_reward(
        session=session,
        user_id=current_user.id,
        reward_id=reward_id,
        request_key=redeem_data.request_key,
    )

    # 幂等重试返回原兑换单时使用 200，新建时 201
    if not created:
        response.status_code = 200

    return redemption

@router.get("/redemptions/mine", response_model=list[RedemptionRead])
def list_my_redemptions(
    offset:int = Query(default=0, ge=0),
    limit:int = Query(default=20, ge=1, le=100),
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    return list_redemptions(
        session,
        current_user.id,
        offset=offset,
        limit=limit,
    )

@router.post("/redemptions/{redemption_id}/cancel", response_model=RedemptionRead)
def cancel_my_redemption(
    redemption_id:int,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    return cancel_redemption(
        session=session,
        user_id=current_user.id,
        redemption_id=redemption_id,
    )
