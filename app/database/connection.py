import asyncpg
import json
from pgvector.asyncpg import register_vector
from typing import Optional
from app.core.config import settings

async def init_connection(conn):
    await register_vector(conn)
    # Register JSON codec to handle JSON/JSONB postgres types automatically
    await conn.set_type_codec(
        'json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog'
    )
    await conn.set_type_codec(
        'jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog'
    )

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                init=init_connection
            )
        except Exception as e:
            print(f"Warning: Could not connect to database at {settings.database_url}: {e}")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()

async def get_db_pool() -> asyncpg.Pool:
    if not db.pool:
        await db.connect()
    return db.pool
