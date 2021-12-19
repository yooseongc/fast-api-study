from typing import List
from os.path import dirname, join
from fastapi import Depends, status, APIRouter, HTTPException, Form
from sqlalchemy import asc
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse

from .auth import get_current_user, TokenUser
from .. import models, schemas
from ..database import get_session

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={status.HTTP_404_NOT_FOUND: {"model": schemas.HttpErrorMessage},
               status.HTTP_401_UNAUTHORIZED: {"model": schemas.HttpErrorMessage}}
)

templates = Jinja2Templates(directory=join(dirname(__file__), '../templates'))


@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_session)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos)\
        .filter(models.Todos.owner_id == user.get("id"))\
        .order_by(asc(models.Todos.complete), asc(models.Todos.priority))\
        .all()
    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})


@router.get("/add-todo", response_class=HTMLResponse)
async def add_new_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})


@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...), description: str = Form(...),
                      priority: int = Form(...), db: Session = Depends(get_session)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_session)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})


@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo_commit(request: Request, todo_id: int, title: str = Form(...),
                           description: str = Form(...), priority: int = Form(...),
                           db: Session = Depends(get_session)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_session)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
        .filter(models.Todos.owner_id == user.get("id")).first()

    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_session)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo.complete = not todo.complete
    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


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
