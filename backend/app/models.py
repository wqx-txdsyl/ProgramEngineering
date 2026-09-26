from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from sqlalchemy import CheckConstraint, UniqueConstraint

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


class PointAccount(SQLModel, table=True):
    __tablename__ = "point_accounts"

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_point_account_balance_non_negative"),
    )

    id:int | None = Field(default=None, primary_key=True)
    user_id:int = Field(foreign_key="users.id", index=True, unique=True)
    balance:int = Field(default=0)

class PointTransaction(SQLModel, table=True):
    __tablename__ = "point_transactions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_type",
            "source_id",
            name="uq_point_transaction_source",
        ),
    )

    id:int | None = Field(default=None, primary_key=True)
    user_id:int = Field(foreign_key="users.id", index=True)
    change:int
    source_type:str = Field(max_length=50)
    source_id:int
    created_at:str = Field(
        max_length=32,
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

class Reward(SQLModel, table=True):
    __tablename__ = "rewards"

    __table_args__ = (
        CheckConstraint("cost > 0", name="ck_reward_cost_positive"),
        CheckConstraint("stock >= 0", name="ck_reward_stock_non_negative"),
    )

    id:int | None = Field(default=None, primary_key=True)
    name:str = Field(max_length=100)
    description:str = Field(max_length=2000, default="")
    cost:int
    stock:int = Field(default=0)
    is_active:bool = Field(default=True)

class Redemption(SQLModel, table=True):
    __tablename__ = "redemptions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "request_key",
            name="uq_redemption_user_request",
        ),
    )

    id:int | None = Field(default=None, primary_key=True)
    user_id:int = Field(foreign_key="users.id", index=True)
    reward_id:int = Field(foreign_key="rewards.id", index=True)
    cost:int
    status:str = Field(default="active", max_length=20)
    request_key:str = Field(max_length=100)
    created_at:str = Field(
        max_length=32,
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
