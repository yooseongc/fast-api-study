from typing import List

from fastapi import Depends, status, APIRouter, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from .auth import get_current_user, TokenUser
from .. import models, schemas
from ..database import get_session

router = APIRouter(
    prefix="/todo",
    tags=["todos"],
    responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
               status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}}
)


@router.get("/", response_model=List[schemas.Todo])
async def read_all(
        user: TokenUser = Depends(get_current_user),
        db: Session = Depends(get_session)):
    return db.query(models.Todos) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .all()


@router.get("/{todo_id}", response_model=schemas.Todo)
async def read_todo(todo_id: int,
                    user: TokenUser = Depends(get_current_user),
                    db: Session = Depends(get_session)):
    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()

    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/", response_model=schemas.Todo, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: schemas.TodoRequest,
                      user: TokenUser = Depends(get_current_user),
                      db: Session = Depends(get_session)):
    todo_model = models.Todos(**todo.dict(), owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()
    return todo_model


@router.put("/{todo_id}", response_model=schemas.Todo)
async def update_todo(todo_id: int,
                      todo: schemas.TodoRequest,
                      user: TokenUser = Depends(get_current_user),
                      db: Session = Depends(get_session)):
    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for k, v in todo.dict().items():
        setattr(todo_model, k, v)

    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)

    return todo_model


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
        todo_id: int,
        user: TokenUser = Depends(get_current_user),
        db: Session = Depends(get_session)):
    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    db.delete(todo_model)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
