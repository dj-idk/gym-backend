from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.coach import (
    CoachCreate,
    CoachRead,
    CoachUpdate,
    ClientCoachRelationCreate,
    ClientCoachRelationRead,
    ProgramCreate,
    ProgramRead,
    ProgramUpdate,
)
from src.service.coach import coach_service
from src.utils.auth import get_current_active_user, get_current_superuser
from src.utils.exceptions import NotFound, Forbidden

router = APIRouter(prefix="/coaches", tags=["coaches"])


# Coach profiles
@router.get("", response_model=List[CoachRead])
async def list_coaches(
    skip: int = 0,
    limit: int = 100,
    specialization: str = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all coaches with optional filtering.
    """
    return await coach_service.get_coaches(db, skip, limit, specialization, is_active)


@router.get("/{coach_id}", response_model=CoachRead)
async def get_coach(coach_id: UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get a specific coach profile.
    """
    return await coach_service.get_coach(db, coach_id)


@router.post("", response_model=CoachRead, status_code=status.HTTP_201_CREATED)
async def create_coach_profile(
    coach_data: CoachCreate,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new coach profile. Admin only.
    """
    return await coach_service.create_coach(db, coach_data)


@router.patch("/{coach_id}", response_model=CoachRead)
async def update_coach_profile(
    coach_id: UUID,
    coach_update: CoachUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a coach profile. Coach or admin only.
    """
    # Check if current user is the coach or an admin
    is_coach = await coach_service.is_user_coach(db, current_user.id, coach_id)
    if not is_coach and not current_user.is_superuser:
        raise Forbidden(detail="Not authorized to update this coach profile")

    return await coach_service.update_coach(db, coach_id, coach_update)


# Client-Coach Relations
@router.post(
    "/relations",
    response_model=ClientCoachRelationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_client_coach_relation(
    relation_data: ClientCoachRelationCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new client-coach relationship.
    """
    return await coach_service.create_client_coach_relation(
        db, current_user.id, relation_data
    )


@router.get("/relations/me", response_model=List[ClientCoachRelationRead])
async def list_my_coach_relations(
    status: str = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all coach relations for the current user.
    """
    return await coach_service.get_client_coach_relations(db, current_user.id, status)


@router.post("/relations/{relation_id}/extend")
async def extend_coach_relation(
    relation_id: UUID,
    days: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Extend a client-coach relationship.
    """
    return await coach_service.extend_client_coach_relation(
        db, current_user.id, relation_id, days
    )


@router.post("/relations/{relation_id}/terminate")
async def terminate_coach_relation(
    relation_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Terminate a client-coach relationship.
    """
    return await coach_service.terminate_client_coach_relation(
        db, current_user.id, relation_id
    )


# Programs
@router.post(
    "/programs", response_model=ProgramRead, status_code=status.HTTP_201_CREATED
)
async def create_program(
    program_data: ProgramCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new training program. Coach only.
    """
    # Verify user is a coach
    coach = await coach_service.get_coach_by_user_id(db, current_user.id)
    if not coach:
        raise Forbidden(detail="Only coaches can create programs")

    return await coach_service.create_program(db, coach.id, program_data)


@router.get("/programs/me", response_model=List[ProgramRead])
async def list_my_programs(
    status: str = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all programs for the current user (as coach or client).
    """
    return await coach_service.get_user_programs(db, current_user.id, status)


@router.patch("/programs/{program_id}", response_model=ProgramRead)
async def update_program(
    program_id: UUID,
    program_update: ProgramUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a training program. Coach only.
    """
    return await coach_service.update_program(
        db, current_user.id, program_id, program_update
    )


@router.post("/programs/{program_id}/assign/{client_id}")
async def assign_program_to_client(
    program_id: UUID,
    client_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Assign a program to a client. Coach only.
    """
    return await coach_service.assign_program_to_client(
        db, current_user.id, program_id, client_id
    )
