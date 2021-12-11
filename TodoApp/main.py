from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.responses import Response

import models
import schemas
from auth import get_current_user, TokenUser
from database import get_db

# models.Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.get("/todo", response_model=List[schemas.Todo])
async def read_all_by_user(
        user: TokenUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Todos).where(models.Todos.owner_id == user.get("id"))
    )
    return result.scalars().all()


@app.get("/todo/{todo_id}",
         response_model=schemas.Todo,
         responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
                    status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def read_todo(todo_id: int,
                    user: TokenUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Todos)
        .where(models.Todos.owner_id == user.get("id"))
        .where(models.Todos.id == todo_id)
    )
    todo_model = result.scalars().first()

    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.post("/todo",
          response_model=schemas.Todo,
          status_code=status.HTTP_201_CREATED,
          responses={status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def create_todo(todo: schemas.TodoRequest,
                      user: TokenUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    todo_model = models.Todos(**todo.dict(), owner_id=user.get("id"))
    async with db.begin():
        db.add(todo_model)
    await db.commit()
    return todo_model


@app.put("/todo/{todo_id}",
         response_model=schemas.Todo,
         responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
                    status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def update_todo(todo_id: int,
                      todo: schemas.TodoRequest,
                      user: TokenUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Todos)
        .where(models.Todos.owner_id == user.get("id"))
        .where(models.Todos.id == todo_id)
    )
    todo_model = result.scalars().first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for k, v in todo.dict().items():
        setattr(todo_model, k, v)

    db.add(todo_model)
    await db.commit()
    await db.refresh(todo_model)

    return todo_model


@app.delete("/todo/{todo_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
                       status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}})
async def delete_todo(
        todo_id: int,
        user: TokenUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Todos)
        .where(models.Todos.owner_id == user.get("id"))
        .where(models.Todos.id == todo_id)
    )
    todo_model = result.scalars().first()

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(todo_model)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
