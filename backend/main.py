from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uuid

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

class Message(BaseModel):
    id: str
    content: str
    role: str

class MessageCreate(BaseModel):
    content: str

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Chat API"}

@app.get("/messages", response_model=List[Message])
async def get_messages():
    return messages_db

@app.post("/messages", response_model=Message)
async def create_message(message: MessageCreate):
    new_message = Message(
        id=str(uuid.uuid4()),
        content=message.content,
        role="user"
    )
    messages_db.append(new_message)
    
    # Simulate AI response
    ai_response = Message(
        id=str(uuid.uuid4()),
        content=f"AI response to: {message.content}",
        role="assistant"
    )
    messages_db.append(ai_response)
    
    return ai_response

@app.put("/messages/{message_id}", response_model=Message)
async def update_message(message_id: str, message: MessageCreate):
    for msg in messages_db:
        if msg.id == message_id:
            msg.content = message.content
            return msg
    raise HTTPException(status_code=404, detail="Message not found")

@app.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: str):
    global messages_db
    messages_db = [msg for msg in messages_db if msg.id != message_id]
    return None