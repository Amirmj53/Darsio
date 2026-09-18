from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_user,
    login_user,
    logout_user,
)


templates = Jinja2Templates(
    directory="templates"
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# --------------------------------------------------
# Register API
# --------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try: 
        return create_user(
            db,
            user_data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )


# --------------------------------------------------
# Login API
# --------------------------------------------------

@router.post("/login")
def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        user_data.email,
        user_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    login_user(
        request,
        user,
    )

    db.commit()

    return {
        "message": "Login successfully"
    }


# --------------------------------------------------
# Register Form
# --------------------------------------------------

@router.post("/register/form")
def register_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
        )

    except ValidationError:
        request.session["auth_error"] = (
            "اطلاعات وارد شده معتبر نیست."
        )

        request.session["register_form"] = {
            "username": username,
            "email": email,
        }

        return RedirectResponse(
            url="/auth/register",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    
    try:
        user = create_user(
            db,
            user_data,
        )

    except ValueError as exc:
        request.session["auth_error"] = str(exc)

        request.session["register_form"] = {
            "username": username,
            "email": email,
        }

        return RedirectResponse(
            url="/auth/register",
            status_code=status.HTTP_303_SEE_OTHER,
        )


    login_user(
        request,
        user,
    )

    db.commit()

    return RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --------------------------------------------------
# Login Form
# --------------------------------------------------

@router.post("/login/form")
def login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        login_data = UserLogin(
            email=email,
            password=password,
        )

    except ValidationError as exc:
            request.session["auth_error"] = (
                "اطلاعات وارد شده معتبر نیست."
            )
    
            return RedirectResponse(
                url="/auth/login",
                status_code=status.HTTP_303_SEE_OTHER
            )

    user = authenticate_user(
        db,
        login_data.email,
        login_data.password,
    )

    if user is None:
        request.session["auth_error"] = (
            "ایمیل یا رمز عبور اشتباه است."
        )

        return RedirectResponse(
            url = "/auth/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    login_user(
        request,
        user,
    )

    db.commit()

    return RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --------------------------------------------------
# Current User
# --------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# --------------------------------------------------
# Logout
# --------------------------------------------------

@router.post("/logout")
def logout(
    request: Request,
):
    logout_user(request)

    return RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# --------------------------------------------------
# Login Page
# --------------------------------------------------

@router.get("/login")
def login_page(
    request: Request,
):

    error = request.session.pop("auth_error", None)

    
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error" : error,
        },
    )


# --------------------------------------------------
# Register Page
# --------------------------------------------------
@router.get("/register")
def register_page(
    request: Request,
):
    error = request.session.pop(
        "auth_error",
        None
    )

    form_data = request.session.pop(
        "register_form",
        {}
    )

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "error": error,
            "form_data": form_data,
        },
    )