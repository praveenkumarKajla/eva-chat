from fastapi import HTTPException
from app.models.schemas import User, UserCreate, UserInDB
from app.utils.security import get_password_hash, verify_password, create_access_token
import uuid
from app.database import get_db_connection

async def get_user(email: str, db):
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)
    if user:
        return UserInDB(**user)

async def register_user(user: UserCreate, db):
    if not user.email or not user.password or not user.first_name or not user.last_name:
        raise HTTPException(status_code=400, detail="All fields are required")
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    db_user = await get_user(user.email, db)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    user_id = uuid.uuid4()
    await db.execute('''
        INSERT INTO users (id, first_name, last_name, email, password)
        VALUES ($1, $2, $3, $4, $5)
    ''', user_id, user.first_name, user.last_name, user.email, hashed_password)
    return User(id=user_id, first_name=user.first_name, last_name=user.last_name, email=user.email)

async def authenticate_user(email: str, password: str, db):
    user = await get_user(email, db)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user