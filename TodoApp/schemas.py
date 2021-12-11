from typing import Optional
from pydantic import BaseModel, Field


class TodoRequest(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, le=5, description="The priority must be between 1-5")
    complete: bool


class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, le=5, description="The priority must be between 1-5")
    complete: bool

    class Config:
        orm_mode = True


class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str


class User(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class HttpErrorMessage(BaseModel):
    detail: str


class TokenMessage(BaseModel):
    access_token: str
    token_type: str




