from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.purchase import PurchaseCreate, PurchaseRead, PurchaseUpdate
from src.service.purchase import purchase_service
from src.utils.auth import get_current_active_user, get_current_superuser
from src.utils.exceptions import NotFound, Forbidden

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
async def create_purchase(
    purchase_data: PurchaseCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new purchase.
    """
    return await purchase_service.create_purchase(db, current_user.id, purchase_data)


@router.get("/current", response_model=List[PurchaseRead])
async def list_my_purchases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    List current user's purchases with optional status filtering.
    """
    return await purchase_service.get_user_purchases(
        db, current_user.id, skip, limit, status
    )


@router.get("/current/{purchase_id}", response_model=PurchaseRead)
async def get_my_purchase(
    purchase_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific purchase for the current user.
    """
    return await purchase_service.get_user_purchase(db, current_user.id, purchase_id)


@router.post("/{purchase_id}/process-payment", response_model=PurchaseRead)
async def process_payment(
    purchase_id: UUID,
    payment_details: dict,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Process payment for a purchase.
    """
    return await purchase_service.process_payment(
        db, current_user.id, purchase_id, payment_details
    )


@router.post("/{purchase_id}/cancel", response_model=PurchaseRead)
async def cancel_purchase(
    purchase_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Cancel a purchase.
    """
    return await purchase_service.cancel_purchase(db, current_user.id, purchase_id)


@router.post("/{purchase_id}/refund", response_model=PurchaseRead)
async def refund_purchase(
    purchase_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refund a purchase. Admin only.
    """
    return await purchase_service.refund_purchase(db, purchase_id)


@router.get("/{purchase_id}/invoice")
async def generate_invoice(
    purchase_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate invoice for a purchase.
    """
    return await purchase_service.generate_invoice(db, current_user.id, purchase_id)


@router.get("", response_model=List[PurchaseRead])
async def list_all_purchases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    user_id: UUID = None,
    service_id: UUID = None,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all purchases with filtering options. Admin only.
    """
    return await purchase_service.get_all_purchases(
        db, skip, limit, status, user_id, service_id
    )
