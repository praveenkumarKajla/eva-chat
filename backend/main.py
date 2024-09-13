from fastapi import FastAPI, HTTPException, Depends, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from database import get_db_connection, init_db, close_db_connections
from models.schemas import User, UserCreate, UserInDB, Token, TokenData, Message, MessageCreate
import uuid
import asyncpg
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta
from uuid import UUID

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Placeholder for database
messages_db = []
users_db = []


@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db_connections(app)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(email: str, db: asyncpg.Connection):
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)
    if user:
        return UserInDB(**user)

async def authenticate_user(email: str, password: str, db: asyncpg.Connection):
    user = await get_user(email, db)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: asyncpg.Connection = Depends(get_db_connection)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        raise credentials_exception
    user = await get_user(email=token_data.email, db=db)
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=User)
async def register(user: UserCreate, db: asyncpg.Connection = Depends(get_db_connection)):
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

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: asyncpg.Connection = Depends(get_db_connection)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/messages", response_model=List[Message])
async def read_messages(current_user: User = Depends(get_current_user), db: asyncpg.Connection = Depends(get_db_connection)):
    rows = await db.fetch('SELECT * FROM messages WHERE sender = $1 ORDER BY timestamp ASC', str(current_user.id))
    return [Message(id=row['id'], content=row['content'], sender=row['sender'], timestamp=row['timestamp'], role=row['role']) for row in rows]


@app.post("/messages", response_model=Message)
async def create_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    message_id = message.id
    new_message = Message(
        id=message_id,
        content=message.content,
        sender=current_user.id,
        timestamp=datetime.now(),
        role='user'
    )
    
    async with db.transaction():
        try:
            await db.execute('''
                INSERT INTO messages (id, content, sender, timestamp, role)
                VALUES ($1, $2, $3, $4, $5)
            ''', new_message.id, new_message.content, current_user.id, new_message.timestamp, new_message.role)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Message with this ID already exists")

    # Generate AI response
    ai_content = f"AI response to: {message.content}"

    # Store AI response in the database
    bot_message_id = uuid.uuid4()
    bot_message = Message(id=bot_message_id, content=ai_content, sender=current_user.id, timestamp=datetime.now(), role='assistant')
    
    try:
        await db.execute('''
            INSERT INTO messages (id, content, sender, timestamp, role)
            VALUES ($1, $2, $3, $4, $5)
        ''', bot_message.id, bot_message.content, current_user.id, bot_message.timestamp, bot_message.role)
    except asyncpg.UniqueViolationError:
        # If this happens, it's extremely unlikely but we should handle it
        raise HTTPException(status_code=500, detail="Failed to create AI response message")

    return bot_message

@app.put("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: str,
    message: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    content = message.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    result = await db.fetchrow('''
        UPDATE messages
        SET content = $1
        WHERE id = $2 AND sender = $3
        RETURNING *
    ''', content, message_id, str(current_user.id))
    
    if result:
        return Message(id=result['id'], content=result['content'], sender=result['sender'], timestamp=result['timestamp'], role=result['role'])
    raise HTTPException(status_code=404, detail="Message not found or not editable")

@app.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    async with db.transaction():
        # Get the timestamp of the message to be deleted
        message = await db.fetchrow('''
            SELECT timestamp FROM messages
            WHERE id = $1 AND sender = $2
        ''', message_id, str(current_user.id))
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found or not deletable")
        
        # Delete the specified message and all subsequent messages
        result = await db.execute('''
            DELETE FROM messages
            WHERE sender = $1 AND timestamp >= $2
        ''', str(current_user.id), message['timestamp'])
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="No messages were deleted")
    return None