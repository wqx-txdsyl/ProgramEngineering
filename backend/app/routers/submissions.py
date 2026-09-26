from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from sqlalchemy import func

from app.database import get_session
from app.dependencies import require_student
from app.models import Submission, Task, User
from app.schemas import (
    SubmissionCreate,
    SubmissionRead,
    SubmissionUpdate,
    LearningProgressRead
)

from app.services.learning import resubmit_submission

router = APIRouter(
    prefix="/api/submissions",
    tags=["submissions"],
)

@router.post("", response_model=SubmissionRead, status_code=201)
def create_submission(
    submission_data: SubmissionCreate,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    task = session.get(Task, submission_data.task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    duplicate_statement = select(Submission).where(
        Submission.task_id == submission_data.task_id,
        Submission.student_id == current_user.id,
    )

    existing_submission = session.exec(duplicate_statement).first()

    if existing_submission is not None:
        raise HTTPException(
            status_code=409,
            detail="You have already submitted for this task",
        )

    submission = Submission(
        task_id=submission_data.task_id,
        student_id=current_user.id,
        content=submission_data.content,
    )

    session.add(submission)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()

        existing_submission = session.exec(duplicate_statement).first()

        if existing_submission is not None:
            raise HTTPException(
                status_code=409,
                detail="You have already submitted for this task",
            )

        raise

    session.refresh(submission)
    return submission

@router.get("/mine", response_model=list[SubmissionRead])
def list_my_submissions(
    offset:int = Query(default=0, ge=0),
    limit:int = Query(default=20, ge=1, le=100),
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    statement = (
        select(Submission)
        .where(Submission.student_id == current_user.id)
        .order_by(Submission.id.desc())
        .offset(offset)
        .limit(limit)
    )

    submissions = session.exec(statement).all()
    return submissions

@router.put("/{submission_id}", response_model=SubmissionRead)
def update_my_submission(
    submission_id:int,
    submission_data: SubmissionUpdate,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student),
):
    submission = resubmit_submission(
        session=session,
        submission_id=submission_id,
        student_id=current_user.id,
        content=submission_data.content,
    )

    return submission

@router.get("/me", response_model=LearningProgressRead)
def get_my_progress(
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student)
):
    statement = (
        select(func.count())
        .select_from(Submission)
        .where(Submission.student_id == current_user.id)
    )
    submission = session.exec(statement).one()

    statement = (
        select(func.count())
        .select_from(Submission)
        .where(
            Submission.student_id == current_user.id,
            Submission.status == "approved"
        )
    )
    progress = session.exec(statement).one()

    return {
        "submitted_count": submission,
        "approved_count": progress
    }

@router.get("/mine/pending", response_model=list[SubmissionRead])
def get_my_pending(
    offset:int = Query(default=0, ge=0),
    limit:int = Query(default=20, ge=1, le=100),
    session:Session = Depends(get_session),
    current_user:User = Depends(require_student)

):
    statement = (
        select(Submission)
        .where(
            Submission.student_id == current_user.id,
            Submission.status == "pending"
        )
        .order_by(Submission.id.desc())
        .offset(offset)
        .limit(limit)
    )

    pending = session.exec(statement).all()

    return pending