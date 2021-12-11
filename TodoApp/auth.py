from typing import NamedTuple, Optional, TypedDict

from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from jose import jwt, JWTError

import models
import schemas
from database import engine, get_db

# key generated using 'openssl.exe rand -hex 32'
SECRET_KEY = "9987eaef63b6d316907e692f4800db4c432a02d21e2edf9e8438443fe4d0f107"
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="http://localhost:9000/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# models.Base.metadata.create_all(bind=engine)
app = FastAPI(debug=True)
origins = ["http://localhost:8000"]
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])


class AuthResult(NamedTuple):
    auth_result: bool
    auth_user: Optional[models.Users]


class TokenUser(TypedDict):
    username: str
    id: int


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str, db: AsyncSession) -> AuthResult:
    result = await db.execute(
        select(models.Users).where(models.Users.username == username)
    )
    user = result.scalars().first()
    if not user:
        return AuthResult(False, None)
    elif not verify_password(password, user.hashed_password):
        return AuthResult(False, user)
    else:
        return AuthResult(True, user)


def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    claims = {
        "sub": username,
        "id": user_id,
        "exp": datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    }
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_bearer)) -> TokenUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise token_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise token_exception()


@app.post("/create/user", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
async def create_new_user(create_user: schemas.CreateUser, db: AsyncSession = Depends(get_db)):
    create_user_model = models.Users(**create_user.dict(exclude={"password"}),
                                     hashed_password=get_password_hash(create_user.password),
                                     is_active=True)
    async with db.begin():
        db.add(create_user_model)
    await db.commit()
    await db.refresh(create_user_model)

    return create_user_model


@app.post("/token",
          response_model=schemas.TokenMessage,
          responses={
              status.HTTP_404_NOT_FOUND: {"description": "User Not Found",
                                          "model": schemas.HttpErrorMessage},
              status.HTTP_401_UNAUTHORIZED: {"description": "User Not Authenticated",
                                             "model": schemas.HttpErrorMessage}
          })
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: AsyncSession = Depends(get_db)):
    auth_res, user = await authenticate_user(form_data.username, form_data.password, db)
    if not auth_res:
        raise get_user_exception()
    else:
        return schemas.TokenMessage(
            access_token=create_access_token(user.username,
                                             user.id,
                                             expires_delta=timedelta(minutes=20)),
            token_type="Bearer"
        )


def get_user_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )


def token_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
