from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.ticket import (
    TicketCreate,
    TicketRead,
    TicketUpdate,
    TicketResponseCreate,
    TicketResponseRead,
)
from src.service.ticket import ticket_service
from src.utils.auth import get_current_active_user, get_current_superuser
from src.utils.exceptions import NotFound, Forbidden

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new support ticket.
    """
    return await ticket_service.create_ticket(db, current_user.id, ticket_data)


@router.get("/me", response_model=List[TicketRead])
async def list_my_tickets(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    category: str = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List tickets created by the current user.
    """
    return await ticket_service.get_user_tickets(
        db, current_user.id, skip, limit, status, category
    )


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific ticket.
    """
    return await ticket_service.get_ticket(db, current_user.id, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a ticket.
    """
    return await ticket_service.update_ticket(
        db, current_user.id, ticket_id, ticket_update
    )


@router.post("/{ticket_id}/responses", response_model=TicketResponseRead)
async def add_ticket_response(
    ticket_id: UUID,
    response_data: TicketResponseCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a response to a ticket.
    """
    return await ticket_service.add_ticket_response(
        db, current_user.id, ticket_id, response_data
    )


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Close a ticket.
    """
    return await ticket_service.close_ticket(db, current_user.id, ticket_id)


@router.post("/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reopen a closed ticket.
    """
    return await ticket_service.reopen_ticket(db, current_user.id, ticket_id)


# Admin endpoints
@router.get("", response_model=List[TicketRead])
async def list_all_tickets(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    category: str = None,
    priority: str = None,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all tickets. Admin only.
    """
    return await ticket_service.get_all_tickets(
        db, skip, limit, status, category, priority
    )


@router.post("/{ticket_id}/assign/{staff_id}")
async def assign_ticket(
    ticket_id: UUID,
    staff_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Assign a ticket to a staff member. Admin only.
    """
    return await ticket_service.assign_ticket(db, ticket_id, staff_id)


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Escalate a ticket.
    """
    return await ticket_service.escalate_ticket(db, current_user.id, ticket_id)


@router.post("/response/{response_id}/attachment")
async def add_response_attachment(
    response_id: UUID,
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add an attachment to a ticket response.
    """
    return await ticket_service.add_response_attachment(
        db, current_user.id, response_id, file
    )
