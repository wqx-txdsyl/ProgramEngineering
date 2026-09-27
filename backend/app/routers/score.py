from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from sqlalchemy import func

from app.database import get_session
from app.dependencies import require_student
from app.models import User, Score
from app.schemas import (
    ScorePost,
    ScoreRead
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
    statement = (
        select(Score)
        .where(
            current_user.id == Score.user_id
        )
    )
    
    new_score = Score(
        user_id=current_user.id,
        score=score.score,
        score_detail=score.score_detail
    )
    session.add(new_score)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()

        existing_score = session.exec(statement).first()

        if existing_score is not None:
            raise HTTPException(
                status_code=409,
                detail="There has been a previous score"
            )
        raise

    session.refresh(new_score)

    return new_score

@router.patch("", response_model=ScorePost, status_code=200)
def update_your_score(
    scoreupdate:ScorePost,
    current_user:User = Depends(require_student),
    session:Session = Depends(get_session)
):
    statement = (
            select(Score)
            .where(
                current_user.id == Score.user_id
            )
        )
    score = session.exec(statement).first()

    if score is None:
        raise HTTPException(
            status_code=404,
            detail="Score Not Found"
        )
    
    score.score = scoreupdate.score
    score.score_detail = scoreupdate.score_detail

    session.commit()
    session.refresh(score)

    return score

@router.get("/record", response_model=list[ScorePost])
def get_my_score(
    current_user:User = Depends(require_teacher),
    session:Session = Depends(get_session)
):
    statement = (
        select(Score)
        .order_by(Score.id)
    )

    score = session.exec(statement).all()
    
    return score

@router.get("", response_model=ScoreRead)
def get_score(
    current_user:User = Depends(require_teacher),
    session:Session = Depends(get_session)
):
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
        "score_one": score_one
    }