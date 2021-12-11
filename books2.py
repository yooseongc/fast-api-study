from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, Query, Request, Response, Form, Header
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.status import HTTP_204_NO_CONTENT, HTTP_418_IM_A_TEAPOT, HTTP_201_CREATED

app = FastAPI()


class Message(BaseModel):
    message: str


class Book(BaseModel):
    id: UUID
    title: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(title="Description of the book", min_length=1, max_length=100)
    rating: int = Field(ge=0, le=100)

    class Config:
        schema_extra = {
            "example": {
                "id": "13c0d7d6-5243-4d0b-99db-c1f6620e6bad",
                "title": "Book Title",
                "author": "Author",
                "description": "Book description",
                "rating": 75
            }
        }


class BookNoRating(BaseModel):
    id: UUID
    title: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, title="Description of the book", min_length=1, max_length=100)

    class Config:
        schema_extra = {
            "example": {
                "id": "13c0d7d6-5243-4d0b-99db-c1f6620e6bad",
                "title": "Book Title",
                "author": "Author",
                "description": "Book description"
            }
        }


BOOKS = []


class NegativeNumberException(Exception):
    def __init__(self, books_to_return: int):
        self.books_to_return = books_to_return


@app.exception_handler(NegativeNumberException)
async def negative_number_exception_handler(request: Request, exception: NegativeNumberException):
    return JSONResponse(
        status_code=HTTP_418_IM_A_TEAPOT,
        content={"message": f"Hey, why do you want {exception.books_to_return} books? You need to read more!"}
    )


@app.get("/", response_model=List[Book])
async def read_all_books(books_to_return: Optional[int] = Query(None, description="돌려 받을 책 수")) -> List[Book]:
    if books_to_return and books_to_return < 0:
        raise NegativeNumberException(books_to_return=books_to_return)
    if len(BOOKS) == 0:
        create_books_no_api()
    if books_to_return and len(BOOKS) >= books_to_return > 0:
        i = 1
        new_books = []
        while i <= books_to_return:
            new_books.append(BOOKS[i - 1])
            i += 1
        return new_books
    return BOOKS


def raise_item_cannot_be_found_exception():
    return JSONResponse(
        status_code=404,
        content={"message": "book cannot be found"},
        headers={"X-Header-Error": "Nothing to be seen at the UUID"}
    )


@app.post("/books/login")
async def book_login(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "password": password}


@app.get("/header")
async def read_header(random_header: Optional[str] = Header(None)):
    return {"Random-Header": random_header}


@app.get("/book/{book_id}", response_model=Book)
async def read_book(book_id: UUID) -> Book:
    for x in BOOKS:
        if x.id == book_id:
            return x
    raise raise_item_cannot_be_found_exception()


@app.get("/book/rating/{book_id}", response_model=BookNoRating)
async def read_book_no_rating(book_id: UUID) -> BookNoRating:
    for x in BOOKS:
        if x.id == book_id:
            return x
    raise raise_item_cannot_be_found_exception()


@app.post("/", status_code=HTTP_201_CREATED, response_model=Book)
async def create_book(book: Book) -> Book:
    BOOKS.append(book)
    return book


@app.put("/{book_id}")
async def update_book(book_id: UUID, book: Book):
    counter = 0
    for x in BOOKS:
        counter += 1
        if x.id == book_id:
            BOOKS[counter - 1] = book
            return book
    raise raise_item_cannot_be_found_exception()


@app.delete("/{book_id}", status_code=204, responses={404: {"model": Message}})
async def delete_book(book_id: UUID):
    counter = 0
    for x in BOOKS:
        counter += 1
        if x.id == book_id:
            del BOOKS[counter - 1]
            return Response(status_code=HTTP_204_NO_CONTENT)
    raise raise_item_cannot_be_found_exception()


def create_books_no_api():
    book1 = Book(id=uuid4(),
                 title="Title 1",
                 author="Author 1",
                 description="Description 1",
                 rating=60)
    book2 = Book(id=uuid4(),
                 title="Title 2",
                 author="Author 2",
                 description="Description 2",
                 rating=70)
    book3 = Book(id=uuid4(),
                 title="Title 3",
                 author="Author 3",
                 description="Description 3",
                 rating=80)
    book4 = Book(id=uuid4(),
                 title="Title 4",
                 author="Author 4",
                 description="Description 4",
                 rating=90)
    BOOKS.append(book1)
    BOOKS.append(book2)
    BOOKS.append(book3)
    BOOKS.append(book4)
