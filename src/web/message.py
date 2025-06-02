from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.message import MessageCreate, MessageRead, MessageList
from src.service.message import message_service
from src.utils.auth import get_current_active_user
from src.utils.exceptions import NotFound, Forbidden

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Send a new message.
    """
    return await message_service.create_message(db, current_user.id, message_data)


@router.get("/inbox", response_model=List[MessageList])
async def get_inbox(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get messages received by the current user.
    """
    return await message_service.get_received_messages(
        db, current_user.id, skip, limit, unread_only
    )


@router.get("/sent", response_model=List[MessageList])
async def get_sent_messages(
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get messages sent by the current user.
    """
    return await message_service.get_sent_messages(db, current_user.id, skip, limit)


@router.get("/{message_id}", response_model=MessageRead)
async def get_message(
    message_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific message.
    """
    return await message_service.get_message(db, current_user.id, message_id)


@router.post("/{message_id}/read")
async def mark_as_read(
    message_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark a message as read.
    """
    return await message_service.mark_as_read(db, current_user.id, message_id)


@router.post("/{message_id}/reply", response_model=MessageRead)
async def reply_to_message(
    message_id: UUID,
    reply_data: MessageCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reply to a message.
    """
    return await message_service.reply_to_message(
        db, current_user.id, message_id, reply_data
    )


@router.post("/attachment")
async def upload_message_attachment(
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload an attachment for a message.
    """
    return await message_service.upload_attachment(db, current_user.id, file)


@router.get("/conversations")
async def get_conversations(
    current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all conversations for the current user.
    """
    return await message_service.get_conversations(db, current_user.id)


@router.get("/conversations/{user_id}")
async def get_conversation_with_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get conversation with a specific user.
    """
    return await message_service.get_conversation(
        db, current_user.id, user_id, skip, limit
    )
