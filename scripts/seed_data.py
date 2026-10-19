import asyncio
import uuid
import sys
import os

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import db, get_db_pool
from app.services.embeddings import generate_embedding

async def seed_documents():
    await db.connect()
    pool = await get_db_pool()

    workspace_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    sample_doc_content = """# Authentication Architecture

We use Redis to handle rate limiting and session storage. The session TTL is currently 24 hours.
All API endpoints must check the Redis cache before querying the primary PostgreSQL database for user details.
"""

    print("Generating embedding for mock document...")
    embedding = await generate_embedding(sample_doc_content)

    print("Inserting mock document into database...")
    async with pool.acquire() as conn:
        # Ensure workspace exists
        await conn.execute(
            "INSERT INTO workspaces (id, name) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
            workspace_id, "Default Workspace"
        )

        await conn.execute(
            """
            INSERT INTO documents (workspace_id, repo_name, file_path, content, last_commit_hash, embedding)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            workspace_id,
            "core-api-repo",
            "docs/architecture/auth.md",
            sample_doc_content,
            "mock-commit-hash",
            embedding
        )
    print("Seed complete.")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_documents())
