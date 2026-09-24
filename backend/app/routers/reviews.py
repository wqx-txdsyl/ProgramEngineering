from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_teacher
from app.models import Submission, Task, User
from app.schemas import SubmissionRead, ReviewCreate
from app.services.learning import review_submission, resubmit_submission

router = APIRouter(
    prefix="/api/reviews",
    tags=["reviews"],
)

@router.get("/pending", response_model=list[SubmissionRead])
def list_pending_submisssions(
    offset:int = Query(default=0, ge=0),
    limit:int = Query(default=20, ge=1, le=100),
    session:Session = Depends(get_session),
    current_user:User = Depends(require_teacher),
):
    statement = (
        select(Submission)
        .where(Submission.status == "pending")
        .offset(offset)
        .limit(limit)
    )

    submissions = session.exec(statement).all()

    return submissions

@router.post("/{submission_id}", response_model=SubmissionRead)
def review_one_submission(
    submission_id:int,
    review_data:ReviewCreate,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_teacher),
):
    submission = review_submission(
        session=session,
        submission_id=submission_id,
        review_data=review_data,
    )

    return submission