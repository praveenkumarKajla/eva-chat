import asyncpg
import os
from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables from .env file
load_dotenv()

async def get_db_connection():
    async with pool.acquire() as connection:
        yield connection
        

async def init_db():
    global pool
    pool = await asyncpg.create_pool(
       os.getenv("DATABASE_URL")
    )

async def close_db_connections(app: FastAPI):
    await pool.close()