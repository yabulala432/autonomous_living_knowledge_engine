from typing import List, Dict, Any
from app.database.connection import get_db_pool

async def find_relevant_documents(embedding: List[float], workspace_id: str, limit: int = 3, similarity_threshold: float = 0.75) -> List[Dict[str, Any]]:
    """
    Finds the most semantically similar documents in the database using cosine similarity via pgvector.
    Only returns documents above the similarity threshold to avoid processing irrelevant files.
    """
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # 1 - (embedding <=> other_embedding) computes cosine similarity
        query = """
            SELECT
                id,
                file_path,
                repo_name,
                content,
                1 - (embedding <=> $1::vector) AS similarity
            FROM documents
            WHERE workspace_id = $2
              AND 1 - (embedding <=> $1::vector) > $3
            ORDER BY embedding <=> $1::vector
            LIMIT $4
        """

        # Because we register_vector(conn) in connection.py,
        # asyncpg will natively encode the python list of floats to pgvector binary.
        records = await conn.fetch(query, embedding, workspace_id, similarity_threshold, limit)

        results = []
        for record in records:
            results.append({
                "id": str(record["id"]),
                "file_path": record["file_path"],
                "repo_name": record["repo_name"],
                "content": record["content"],
                "similarity": record["similarity"]
            })

        return results
