from fastapi import HTTPException
from sqlalchemy import update
from sqlmodel import Session

from app.models import Submission
from app.schemas import ReviewCreate

def review_submission(
        session: Session,
        submission_id: int,
        review_data: ReviewCreate,
) -> Submission:
    submission = session.get(Submission, submission_id)

    if submission is None:
        raise HTTPException(
            status_code=404,
            detail="Submission not found",
        )

    statement = (
        update(Submission)
        .where(
            Submission.id == submission_id,
            Submission.status == "pending",
            )
        .values(
            status=review_data.decision,
            feedback=review_data.feedback,
        )
        .execution_options(synchronize_session=False)
    )

    result = session.execute(statement)

    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Submission has already been reviewed",
        )

    session.commit()
    session.refresh(submission)

    return submission

def resubmit_submission(
        session: Session,
        submission_id: int,
        student_id: int,
        content: str,
) -> Submission:
    submission = session.get(Submission, submission_id)

    if submission is None or submission.student_id != student_id:
        raise HTTPException(
            status_code=404,
            detail="Submission not found",
        )

    statement = (
        update(Submission)
        .where(
            Submission.id == submission_id,
            Submission.student_id == student_id,
            Submission.status == "rejected",
        )
        .values(
            content=content,
            status="pending",
            feedback="",
        )
        .execution_options(synchronize_session=False)
    )

    result = session.execute(statement)

    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Submission cannot be resubmitted",
        )
    session.commit()
    session.refresh(submission)

    return submission