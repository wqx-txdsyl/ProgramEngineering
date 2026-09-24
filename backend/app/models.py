from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id:int | None = Field(default=None, primary_key=True)
    title:str = Field(max_length=100)
    description:str = Field(max_length=2000, default="")

class User(SQLModel, table=True):
    __tablename__ = "users"

    id:int | None = Field(default=None, primary_key=True)
    username: str = Field(
        index=True,
        unique=True,
        max_length=50
    )
    password_hash: str = Field(max_length=255)
    role:str = Field(default="student", max_length=20)

class Submission(SQLModel, table=True):
    __tablename__ = "submissions"

    __table_args__ = (
        UniqueConstraint(
            "task_id", 
            "student_id", 
            name="uq_submission_task_student"
            ),
    )

    id:int | None = Field(default=None, primary_key=True)
    task_id:int = Field(foreign_key="tasks.id", index=True)
    student_id:int = Field(foreign_key="users.id", index=True)
    content:str = Field(max_length=2000)
    status:str = Field(default="pending", max_length=20)
    feedback:str = Field(default="", max_length=2000)