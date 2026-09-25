from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user, require_teacher
from app.models import Task, User
from app.schemas import TaskCreate, TaskRead, TaskDescriptionUpdate, TaskRename

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
)

@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    task_data: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_teacher),
):
    task = Task(
        title=task_data.title,
        description=task_data.description
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return task

@router.get("", response_model=list[TaskRead])
def list_tasks(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = (
        select(Task)
        .order_by(Task.id)
        .offset(offset)
        .limit(limit)
    )

    tasks = session.exec(statement).all()
    return tasks

@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task = session.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task Not Found"
        )

    return task

@router.patch("/{task_id}", response_model=TaskRead)
def rename_task(
    task_id:int,
    task_data:TaskRename,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_teacher)
):
    task = session.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task Not Found"
        )

    task.title = task_data.title
    session.commit()
    session.refresh(task)

    return task

@router.patch("/{task_id}/description", response_model=TaskRead)
def modify_description(
    task_id:int,
    description_data:TaskDescriptionUpdate,
    session:Session = Depends(get_session),
    current_user:User = Depends(require_teacher)
):
    task = session.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task Not Found"
        )

    task.description = description_data.description
    session.commit()
    session.refresh(task)

    return task