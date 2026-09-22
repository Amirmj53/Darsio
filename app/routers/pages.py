from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(tags=["Pages"])

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": None
        }
    )


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/dashboard/c/{public_id}", response_class=HTMLResponse)
def dashboard(
    request: Request,
    public_id:str | None = None,
    current_user: User = Depends(get_current_user)
):

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_user": current_user,
            "initial_public_id" : public_id,
        }
    )

def require_admin_user(user:User) -> User | RedirectResponse:
    if not user.is_active or not (user.is_admin or user.is_superadmin):
        return RedirectResponse(url="/dashboard", status_code=302)
    return user

@router.get("/admin", response_class=HTMLResponse)
def admin_panel(
    request:Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active or not(
        current_user.is_admin or current_user.is_superadmin
    ):
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"current_user" : current_user},
    )