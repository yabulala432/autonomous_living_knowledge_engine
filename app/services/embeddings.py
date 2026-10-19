from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def generate_embedding(text: str) -> List[float]:
    """
    Generates a 1536-dimensional embedding for the given text using text-embedding-3-small.
    """
    if not text.strip():
        # Return a zero vector if there is no text
        return [0.0] * 1536

    response = await client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
