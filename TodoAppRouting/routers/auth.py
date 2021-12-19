from datetime import datetime, timedelta
from os.path import join, dirname
from typing import NamedTuple, Optional, TypedDict

from fastapi import Depends, status, HTTPException, APIRouter, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from TodoAppRouting import models
from TodoAppRouting import schemas
from TodoAppRouting.database import get_session

# key generated using 'openssl.exe rand -hex 32'
SECRET_KEY = "9987eaef63b6d316907e692f4800db4c432a02d21e2edf9e8438443fe4d0f107"
ALGORITHM = "HS256"
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

templates = Jinja2Templates(directory=join(dirname(__file__), '../templates'))
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={status.HTTP_401_UNAUTHORIZED: {"user": "Not authorized"}}
)


class LoginForm:

    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")


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


def authenticate_user(username: str, password: str, db: Session) -> AuthResult:
    user = db.query(models.Users) \
        .filter(models.Users.username == username) \
        .first()
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


async def get_current_user(request: Request) -> Optional[TokenUser]:
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise token_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise token_exception()


@router.post("/create/user",
             status_code=status.HTTP_201_CREATED,
             response_model=schemas.User)
async def create_new_user(create_user: schemas.CreateUser, db: Session = Depends(get_session)):
    create_user_model = models.Users(**create_user.dict(exclude={"password"}),
                                     hashed_password=get_password_hash(create_user.password),
                                     is_active=True)
    db.add(create_user_model)
    db.commit()
    return create_user_model


@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_session)):
    auth_res, user = authenticate_user(form_data.username, form_data.password, db)
    if not auth_res:
        return False
    token = create_access_token(user.username, user.id, expires_delta=timedelta(minutes=60))
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_session)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)
        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.get("/logout")
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, email: str = Form(...), username: str = Form(...),
                        firstname: str = Form(...), lastname: str = Form(...),
                        password: str = Form(...), password2: str = Form(...),
                        db: Session = Depends(get_session)):

    validation1 = db.query(models.Users).filter(models.Users.username == username).first()
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration request"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

    user_model = models.Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname

    hash_password = get_password_hash(password)
    user_model.hashed_password = hash_password
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg = "User successfully created"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


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
