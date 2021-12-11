from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.responses import Response

import models
import schemas
from auth import get_current_user, get_user_exception, TokenUser
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/todo", response_model=List[schemas.Todo])
async def read_all_by_user(
        user: TokenUser = Depends(get_current_user),
        db: Session = Depends(get_db)):
    return db.query(models.Todos)\
        .filter(models.Todos.owner_id == user.get("id"))\
        .all()


@app.get("/todo/{todo_id}",
         response_model=schemas.Todo,
         responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
                    status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def read_todo(todo_id: int,
                    user: TokenUser = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .filter(models.Todos.id == todo_id) \
        .first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.post("/todo",
          response_model=schemas.Todo,
          status_code=status.HTTP_201_CREATED,
          responses={status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def create_todo(todo: schemas.TodoRequest,
                      user: TokenUser = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    todo_model = models.Todos(**todo.dict(), owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)

    return todo_model


@app.put("/todo/{todo_id}",
         response_model=schemas.Todo,
         responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
                    status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def update_todo(todo_id: int,
                      todo: schemas.TodoRequest,
                      user: TokenUser = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .filter(models.Todos.id == todo_id)\
        .first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for k, v in todo.dict().items():
        setattr(todo_model, k, v)
    db.add(todo_model)
    db.commit()

    return todo_model


@app.delete("/todo/{todo_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
                       status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def delete_todo(
        todo_id: int,
        user: TokenUser = Depends(get_current_user),
        db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    db.delete(todo_model)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

