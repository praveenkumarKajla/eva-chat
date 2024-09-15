import asyncpg
from app.config import DATABASE_URL

async def get_db_connection():
    async with pool.acquire() as connection:
        yield connection

async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

async def close_db_connections(app):
    await pool.close()