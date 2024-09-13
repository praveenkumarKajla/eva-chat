from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from uuid import UUID

# Secret key for JWT
SECRET_KEY = "your-secret-key"  # Replace with a secure secret key
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

class Message(BaseModel):
    id: str
    content: str
    sender: UUID
    timestamp: datetime
    role: str

class MessageCreate(BaseModel):
    content: str
    id: str

# User models
class User(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserInDB(User):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(email: str):
    for user in users_db:
        if user.email == email:
            return user
    return None

def authenticate_user(email: str, password: str):
    user = get_user(email)
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

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    if get_user(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = UserInDB(**user.dict(exclude={"password"}), id=uuid.uuid4(), password=hashed_password)
    users_db.append(new_user)
    return new_user

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
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
async def get_messages(current_user: User = Depends(get_current_user)):
    return messages_db

@app.post("/messages", response_model=Message)
async def create_message(message: MessageCreate, current_user: User = Depends(get_current_user)):
    new_message = Message(
        id=message.id,
        content=message.content,
        sender=str(current_user.id),
        timestamp=datetime.utcnow(),
        role="user"
    )
    messages_db.append(new_message)
    
    # Simulate AI response
    ai_response = Message(
        id=str(uuid.uuid4()),
        content=f"AI response to: {message.content}",
        sender=str(current_user.id),
        timestamp=datetime.utcnow(),
        role="assistant"
    )
    messages_db.append(ai_response)
    
    return ai_response

@app.put("/messages/{message_id}", response_model=Message)
async def update_message(message_id: str, message: MessageCreate, current_user: User = Depends(get_current_user)):
    for msg in messages_db:
        if msg.id == message_id and msg.sender == str(current_user.id):
            msg.content = message.content
            return msg
    raise HTTPException(status_code=404, detail="Message not found")

@app.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: str, current_user: User = Depends(get_current_user)):
    global messages_db
    messages_db = [msg for msg in messages_db if not (msg.id == message_id and msg.sender == str(current_user.id))]
    return None