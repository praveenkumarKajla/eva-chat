from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import Message, MessageCreate, User
from datetime import datetime
import uuid
import json
from app.utils.chatbot import get_chatbot_response
import asyncpg
import logging
from app.database import get_db_connection

logger = logging.getLogger(__name__)

async def get_user_messages(current_user: User, db):
    rows = await db.fetch('SELECT * FROM messages WHERE sender = $1 ORDER BY timestamp ASC', str(current_user.id))
    return [Message(id=row['id'], content=row['content'], sender=row['sender'], timestamp=row['timestamp'], role=row['role']) for row in rows]

async def create_user_message(message: MessageCreate, current_user: User, db, background_tasks):
    message_id = message.id
    new_message = Message(
        id=message_id,
        content=message.content,
        sender=current_user.id,
        timestamp=datetime.now(),
        role='user'
    )
    
    try:
        async with db.transaction():
            await db.execute('''
                INSERT INTO messages (id, content, sender, timestamp, role)
                VALUES ($1, $2, $3, $4, $5)
            ''', new_message.id, new_message.content, current_user.id, new_message.timestamp, new_message.role)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Message with this ID already exists")
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    bot_message_id = str(uuid.uuid4())
    bot_message_content = ""

    async def event_generator():
        nonlocal bot_message_content
        async for token in get_chatbot_response(new_message.content):
            bot_message_content += token
            yield f"data: {json.dumps({'id': bot_message_id, 'content': token, 'role': 'assistant'})}\n\n"

    async def save_bot_message():
        try:
            async for new_db in get_db_connection():
                try:
                    async with new_db.transaction():
                        await new_db.execute('''
                            INSERT INTO messages (id, content, sender, timestamp, role)
                            VALUES ($1, $2, $3, $4, $5)
                        ''', bot_message_id, bot_message_content, str(current_user.id), datetime.now(), 'assistant')
                    break  # Exit the loop after successful execution
                except Exception as e:
                    logger.error(f"Error saving bot message: {e}")
                finally:
                    await new_db.close()
        except Exception as e:
            logger.error(f"Unhandled error in save_bot_message: {e}")

    background_tasks.add_task(save_bot_message)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def update_user_message(message_id: str, message: dict, current_user: User, db):
    try:
        content = message.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        result = await db.fetchrow('''
            UPDATE messages
            SET content = $1
            WHERE id = $2 AND sender = $3
            RETURNING *
        ''', content, message_id, current_user.id)
        
        if result:
            return Message(id=result['id'], content=result['content'], sender=result['sender'], timestamp=result['timestamp'], role=result['role'])
        raise HTTPException(status_code=404, detail="Message not found or not editable")
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def delete_user_message(message_id: str, current_user: User, db):
    async with db.transaction():
        message = await db.fetchrow('''
            SELECT timestamp FROM messages
            WHERE id = $1 AND sender = $2
        ''', message_id, str(current_user.id))
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found or not deletable")
        
        result = await db.execute('''
            DELETE FROM messages
            WHERE sender = $1 AND timestamp >= $2
        ''', str(current_user.id), message['timestamp'])
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="No messages were deleted")