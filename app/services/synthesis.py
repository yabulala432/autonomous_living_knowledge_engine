from typing import List, Dict, Any
from datetime import datetime, timedelta
from openai import AsyncOpenAI

from app.core.config import settings
from app.database.connection import get_db_pool
from app.core.prompts import SPRINT_SYNTHESIS_SYSTEM_PROMPT, SPRINT_SYNTHESIS_USER_PROMPT

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def generate_sprint_digest(workspace_id: str, days_back: int = 7) -> str:
    """
    Queries recent technical decisions and synthesizes them into an executive sprint digest.
    """
    pool = await get_db_pool()

    # 1. Fetch recent decisions
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT title, rationale, impacted_scope, created_at
            FROM decisions
            WHERE workspace_id = $1
              AND created_at >= NOW() - $2::interval
            ORDER BY created_at DESC
            """,
            workspace_id,
            timedelta(days=days_back)
        )

    if not records:
        return "No architectural decisions were recorded in the specified timeframe."

    # 2. Format decisions for the LLM
    decisions_text = ""
    for r in records:
        scope = ", ".join(r['impacted_scope']) if r['impacted_scope'] else "None"
        date = r['created_at'].strftime("%Y-%m-%d")
        decisions_text += f"- [{date}] **{r['title']}**: {r['rationale']} (Impacts: {scope})\n"

    # 3. Call LLM to synthesize the report
    user_prompt = SPRINT_SYNTHESIS_USER_PROMPT.format(
        days_back=days_back,
        decisions_text=decisions_text
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SPRINT_SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    return response.choices[0].message.content
