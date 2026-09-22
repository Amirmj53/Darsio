from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ticket import TicketDetail, TicketListItem
from app.services import tickets as tickets_service


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketListItem, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    category: str = Form(...),
    description: str = Form(...),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = await tickets_service.create_ticket(
        db, current_user, category, description, file
    )
    return tickets_service._ticket_dict(ticket)


@router.get("", response_model=list[TicketListItem])
def list_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [
        tickets_service._ticket_dict(t)
        for t in tickets_service.list_user_tickets(db, current_user)
    ]


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = tickets_service.get_user_ticket(db, current_user, ticket_id)
    return tickets_service._ticket_detail_dict(ticket)
