"""积分与兑换业务（C 同学维护，docs/data-points-tasks.md §2–§4）。

事务约定：
- 本模块函数与调用方共用同一个 Session；除 redeem_reward / cancel_redemption
  在全部写入成功后统一 commit 外，其余函数只写入不提交。
- 审核奖励由 services/learning.py 的 review_submission 在同一事务内调用，
  任何一步失败整体回滚，不会出现"审核成功但积分失败"。
- 防重复依赖数据库唯一约束（point_transactions 的来源三元组、
  redemptions 的 user_id + request_key），不依赖"先查有没有"。
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import PointAccount, PointTransaction, Redemption, Reward

# 审核奖励分值：团队确认后在此统一调整（docs/data-points-tasks.md §2）
REVIEW_APPROVED_POINTS = 10

SOURCE_REVIEW_APPROVED = "review_approved"
SOURCE_REDEEM = "redeem"
SOURCE_REFUND = "refund"

REDEMPTION_ACTIVE = "active"
REDEMPTION_CANCELLED = "cancelled"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_or_create_account(session: Session, user_id: int) -> PointAccount:
    account = session.exec(
        select(PointAccount).where(PointAccount.user_id == user_id)
    ).first()

    if account is None:
        account = PointAccount(user_id=user_id, balance=0)
        session.add(account)
        session.flush()

    return account


def get_balance(session: Session, user_id: int) -> int:
    account = session.exec(
        select(PointAccount).where(PointAccount.user_id == user_id)
    ).first()
    return account.balance if account is not None else 0


def _apply_balance_change(
    session: Session,
    user_id: int,
    delta: int,
    require_at_least: int | None = None,
) -> bool:
    """带条件的余额更新；delta 为负时要求当前余额足够。返回是否更新成功。"""
    get_or_create_account(session, user_id)

    statement = update(PointAccount).where(PointAccount.user_id == user_id)

    if require_at_least is not None:
        statement = statement.where(PointAccount.balance >= require_at_least)

    statement = statement.values(
        balance=PointAccount.balance + delta
    ).execution_options(synchronize_session=False)

    return session.execute(statement).rowcount == 1


def award_review_points(
    session: Session,
    submission_id: int,
    student_id: int,
) -> None:
    """审核通过的奖励：同事务写入余额与流水，由调用方（review_submission）统一提交。

    唯一约束 (user_id, source_type, source_id) 保证一条成果最多奖励一次；
    冲突时抛 409，调用方回滚整个审核事务。
    """
    _apply_balance_change(session, student_id, REVIEW_APPROVED_POINTS)

    session.add(PointTransaction(
        user_id=student_id,
        change=REVIEW_APPROVED_POINTS,
        source_type=SOURCE_REVIEW_APPROVED,
        source_id=submission_id,
    ))

    try:
        session.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Review reward already issued for this submission",
        )


def list_transactions(
    session: Session,
    user_id: int,
    offset: int = 0,
    limit: int = 20,
) -> list[PointTransaction]:
    return list(session.exec(
        select(PointTransaction)
        .where(PointTransaction.user_id == user_id)
        .order_by(PointTransaction.id.desc())
        .offset(offset)
        .limit(limit)
    ).all())


def redeem_reward(
    session: Session,
    user_id: int,
    reward_id: int,
    request_key: str,
) -> tuple[Redemption, bool]:
    """兑换奖励。余额、库存、兑换单、流水在同一事务内更新。

    幂等：同一 (user_id, request_key) 重试返回原兑换单且不再扣费；
    同一键搭配不同奖励返回 409。失败路径统一回滚后抛错，不留任何写入。
    返回 (兑换单, 是否新创建)。
    """
    existing = session.exec(
        select(Redemption).where(
            Redemption.user_id == user_id,
            Redemption.request_key == request_key,
        )
    ).first()

    if existing is not None:
        if existing.reward_id != reward_id:
            raise HTTPException(
                status_code=409,
                detail="Request key was already used for a different reward",
            )
        return existing, False

    reward = session.get(Reward, reward_id)

    if reward is None:
        raise HTTPException(
            status_code=404,
            detail="Reward not found",
        )

    if not reward.is_active:
        raise HTTPException(
            status_code=409,
            detail="Reward is not available",
        )

    stock_result = session.execute(
        update(Reward)
        .where(
            Reward.id == reward_id,
            Reward.stock > 0,
        )
        .values(stock=Reward.stock - 1)
        .execution_options(synchronize_session=False)
    )

    if stock_result.rowcount != 1:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Reward is out of stock",
        )

    if not _apply_balance_change(
        session,
        user_id,
        -reward.cost,
        require_at_least=reward.cost,
    ):
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Insufficient balance",
        )

    redemption = Redemption(
        user_id=user_id,
        reward_id=reward_id,
        cost=reward.cost,
        status=REDEMPTION_ACTIVE,
        request_key=request_key,
    )
    session.add(redemption)
    session.flush()

    session.add(PointTransaction(
        user_id=user_id,
        change=-redemption.cost,
        source_type=SOURCE_REDEEM,
        source_id=redemption.id,
    ))

    session.commit()
    session.refresh(redemption)
    return redemption, True


def cancel_redemption(
    session: Session,
    user_id: int,
    redemption_id: int,
) -> Redemption:
    """取消未使用的兑换单：退积分、恢复库存。仅 active 可取消，退款只发生一次。"""
    redemption = session.get(Redemption, redemption_id)

    if redemption is None or redemption.user_id != user_id:
        raise HTTPException(
            status_code=404,
            detail="Redemption not found",
        )

    result = session.execute(
        update(Redemption)
        .where(
            Redemption.id == redemption_id,
            Redemption.status == REDEMPTION_ACTIVE,
        )
        .values(status=REDEMPTION_CANCELLED)
        .execution_options(synchronize_session=False)
    )

    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Redemption cannot be cancelled",
        )

    session.add(PointTransaction(
        user_id=user_id,
        change=redemption.cost,
        source_type=SOURCE_REFUND,
        source_id=redemption_id,
    ))

    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Refund already issued for this redemption",
        )

    session.execute(
        update(Reward)
        .where(Reward.id == redemption.reward_id)
        .values(stock=Reward.stock + 1)
        .execution_options(synchronize_session=False)
    )

    _apply_balance_change(session, user_id, redemption.cost)

    session.commit()
    session.refresh(redemption)
    return redemption


def list_rewards(
    session: Session,
    offset: int = 0,
    limit: int = 20,
) -> list[Reward]:
    return list(session.exec(
        select(Reward)
        .where(Reward.is_active == True)  # noqa: E712  只展示可兑换奖励
        .order_by(Reward.id)
        .offset(offset)
        .limit(limit)
    ).all())


def list_redemptions(
    session: Session,
    user_id: int,
    offset: int = 0,
    limit: int = 20,
) -> list[Redemption]:
    return list(session.exec(
        select(Redemption)
        .where(Redemption.user_id == user_id)
        .order_by(Redemption.id.desc())
        .offset(offset)
        .limit(limit)
    ).all())
