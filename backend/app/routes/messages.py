from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Body
from typing import List
from app.models.schemas import Message, MessageCreate, User
from app.services.message_service import (
    get_user_messages,
    create_user_message,
    update_user_message,
    delete_user_message,
)
from app.database import get_db_connection
from app.utils.security import get_current_user
from app.utils.limiter import limiter

router = APIRouter()

@router.get("/messages", response_model=List[Message])
async def read_messages(current_user: User = Depends(get_current_user), db=Depends(get_db_connection)):
    return await get_user_messages(current_user, db)

@router.post("/messages", response_model=Message)
@limiter.limit("50/minute")
async def create_message(
    request: Request,
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db_connection),
):
    return await create_user_message(message, current_user, db, background_tasks)

@router.put("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: str,
    message: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    return await update_user_message(message_id, message, current_user, db)

@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    await delete_user_message(message_id, current_user, db)
    return None