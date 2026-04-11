import asyncpg
import asyncio
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
"""

async def init():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(CREATE_USERS_TABLE)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(init())
