from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from sqlalchemy import func
from pydantic import Field

from app.database import get_session
from app.dependencies import require_student
from app.models import User, Score
from app.schemas import (
    ScorePost,
    ScoreRead,
    ScoreReadMine
)
from app.dependencies import get_current_user, require_teacher, require_student

router = APIRouter(
    prefix="/api/scores",
    tags=["scores"],
)

@router.post("", response_model=ScorePost, status_code=201)
def post_your_score(
    score:ScorePost,
    current_user:User = Depends(require_student),
    session:Session = Depends(get_session)
):
    new_score = Score(
        user_id=current_user.id,
        score=score.score
    )
    session.add(new_score)
    session.commit()
    session.refresh(new_score)

    return new_score

@router.get("/me", response_model=list[ScoreReadMine])
def get_my_score(
    current_user:User = Depends(require_student),
    session:Session = Depends(get_session)
):
    statement = (
        select(Score)
        .where(current_user.id==Score.user_id)
        .order_by(Score.id.desc())
    )

    score = session.exec(statement).all()
    score_one = session.exec(statement).first()

    if score_one is None:
        raise HTTPException(
            status_code=404,
            detail="Score Not Found"
        )

    return score

@router.get("", response_model=ScoreRead)
def get_score(
    current_user:User = Depends(require_teacher),
    session:Session = Depends(get_session)
):
    statement_zero =(
        select(func.count())
        .select_from(Score)
        .where(Score.score == 0)
    )
    score_zero = session.exec(statement_zero).one()

    statement_one = (
        select(func.count())
        .select_from(Score)
        .where(Score.score == 1)
    )
    score_one = session.exec(statement_one).one()

    statement_two = (
        select(func.count())
        .select_from(Score)
        .where(Score.score == 2)
    )
    score_two = session.exec(statement_two).one()

    statement_three = (
        select(func.count())
        .select_from(Score)
        .where(Score.score == 3)
    )
    score_three = session.exec(statement_three).one()

    statement_four = (
        select(func.count())
        .select_from(Score)
        .where(Score.score == 4)
    )
    score_four = session.exec(statement_four).one()

    statement_five = (
        select(func.count())
        .select_from(Score)
        .where(Score.score == 5)
    )
    score_five = session.exec(statement_five).one()

    statement_count = (
        select(func.count())
        .select_from(Score)
    )
    count = session.exec(statement_count).one()

    statement_sum = (
        select(func.sum(Score.score))
        .select_from(Score)
    )
    sum = session.exec(statement_sum).one()

    if count == 0:
        average = 0.0
    else:
        average = float(sum/count)

    return{
        "score_average": average,
        "score_five": score_five,
        "score_four": score_four,
        "score_three": score_three,
        "score_two": score_two,
        "score_one": score_one,
        "score_zero": score_zero
    }