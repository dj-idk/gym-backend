from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.service import (
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
    ServiceCategoryCreate,
    ServiceCategoryRead,
    ServiceCategoryUpdate,
)
from src.service.service import service_service
from src.utils.auth import get_current_active_user, get_current_superuser
from src.utils.exceptions import NotFound

router = APIRouter(prefix="/services", tags=["services"])


# Service Categories
@router.get("/categories", response_model=List[ServiceCategoryRead])
async def list_service_categories(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List all service categories.
    """
    return await service_service.get_categories(db, skip, limit)


@router.get("/categories/{category_id}", response_model=ServiceCategoryRead)
async def get_service_category(
    category_id: UUID, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific service category.
    """
    return await service_service.get_category(db, category_id)


@router.post(
    "/categories",
    response_model=ServiceCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_category(
    category_data: ServiceCategoryCreate,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new service category. Admin only.
    """
    return await service_service.create_category(db, category_data)


@router.patch("/categories/{category_id}", response_model=ServiceCategoryRead)
async def update_service_category(
    category_id: UUID,
    category_update: ServiceCategoryUpdate,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a service category. Admin only.
    """
    return await service_service.update_category(db, category_id, category_update)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_category(
    category_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a service category. Admin only.
    """
    await service_service.delete_category(db, category_id)
    return None


# Services
@router.get("", response_model=List[ServiceRead])
async def list_services(
    skip: int = 0,
    limit: int = 100,
    category_id: UUID = None,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all services with optional filtering.
    """
    return await service_service.get_services(db, skip, limit, category_id, is_active)


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(service_id: UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get a specific service.
    """
    return await service_service.get_service(db, service_id)


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new service. Admin only.
    """
    return await service_service.create_service(db, service_data)


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: UUID,
    service_update: ServiceUpdate,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a service. Admin only.
    """
    return await service_service.update_service(db, service_id, service_update)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a service. Admin only.
    """
    await service_service.delete_service(db, service_id)
    return None


@router.post("/{service_id}/activate")
async def activate_service(
    service_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Activate a service. Admin only.
    """
    return await service_service.activate_service(db, service_id)


@router.post("/{service_id}/deactivate")
async def deactivate_service(
    service_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Deactivate a service. Admin only.
    """
    return await service_service.deactivate_service(db, service_id)


@router.get("/{service_id}/availability")
async def check_service_availability(
    service_id: UUID, date: str, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Check if a service is available on a specific date.
    """
    return await service_service.check_availability(db, service_id, date)
