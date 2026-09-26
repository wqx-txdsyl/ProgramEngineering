from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class TaskCreate(BaseModel):
    model_config  = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title:str = Field(min_length=1, max_length=100)
    description:str = Field(min_length=0, max_length=2000, default="")

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    title:str
    description:str

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username:str = Field(min_length=1, max_length=50)
    password:str = Field(min_length=1, max_length=128)

class TokenRead(BaseModel):
    access_token:str
    token_type:str = "bearer"

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    username:str
    role:str

class SubmissionCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    task_id:int = Field(gt=0)
    content:str = Field(min_length=1, max_length=2000)

class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    task_id:int = Field(gt=0)
    student_id:int = Field(gt=0)
    content:str
    status:str
    feedback:str

class ReviewCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    decision:Literal["approved", "rejected"]
    feedback:str = Field(min_length=1, max_length=2000)

class SubmissionUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    content:str = Field(min_length=1, max_length=2000)

class TaskRename(BaseModel):
    model_config = ConfigDict(
            str_strip_whitespace=True,
            extra="forbid"
        )

    title:str = Field(min_length=1, max_length=100)

class TaskDescriptionUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    description:str = Field(min_length=1, max_length=2000)

class LearningProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submitted_count:int = Field(ge=0)
    approved_count:int = Field(ge=0)

class Register(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    username:str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password:str = Field(min_length=8, max_length=128)



class PointBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id:int
    balance:int

class PointTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    user_id:int
    change:int
    source_type:str
    source_id:int
    created_at:str

class RewardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    name:str
    description:str
    cost:int
    stock:int
    is_active:bool

class RedeemRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    request_key:str = Field(min_length=1, max_length=100)

class RedemptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    user_id:int
    reward_id:int
    cost:int
    status:str
    request_key:str
    created_at:str