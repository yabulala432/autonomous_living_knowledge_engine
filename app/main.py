import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from typing import Dict, Any

from app.database.connection import db, get_db_pool
from app.services.extractor import extract_decision
from app.services.embeddings import generate_embedding

app = FastAPI(title="Autonomous Living Knowledge Engine MVP")

@app.on_event("startup")
async def startup_event():
    await db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()

async def process_event(event_source: str, payload: Dict[Any, Any]):
    """Background task to extract and store decisions from events."""
    pool = await get_db_pool()

    # 1. Insert raw event
    # Mocking workspace_id for the MVP
    workspace_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    source_id = ""
    author = ""
    raw_content = ""
    timestamp = datetime.now(timezone.utc).isoformat()

    if event_source == "github":
        source_id = payload.get("pull_request", {}).get("url", "unknown_pr")
        author = payload.get("sender", {}).get("login", "unknown_author")
        raw_content = payload.get("pull_request", {}).get("body", "")
    elif event_source == "slack":
        source_id = payload.get("event", {}).get("ts", "unknown_ts")
        author = payload.get("event", {}).get("user", "unknown_user")
        raw_content = payload.get("event", {}).get("text", "")

    async with pool.acquire() as conn:
        # We need a workspace to exist for the foreign key, so we'll do an upsert or ignore it in MVP logic.
        # For simplicity here, we assume a workspace exists or we skip the FK constraint if not strictly needed in tests,
        # but to be safe we'll insert a dummy workspace if it doesn't exist.
        await conn.execute(
            "INSERT INTO workspaces (id, name) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
            workspace_id, "Default Workspace"
        )

        event_id = await conn.fetchval(
            """
            INSERT INTO ingested_events (workspace_id, source, source_id, author, raw_payload)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            workspace_id, event_source, source_id, author, payload
        )

        # 2. Extract decision using LLM
        try:
            decision = await extract_decision(
                event_source=event_source,
                author_handle=author,
                timestamp=timestamp,
                raw_event_content=raw_content
            )
        except Exception as e:
            print(f"Error during LLM extraction: {e}")
            return

        # 3. If architectural decision, compute embedding and save to DB
        if decision.is_architectural_decision:
            embedding = await generate_embedding(decision.rationale)

            await conn.execute(
                """
                INSERT INTO decisions (workspace_id, event_id, title, rationale, impacted_scope, embedding)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                workspace_id, event_id, decision.title, decision.rationale, decision.impacted_systems, embedding
            )


@app.post("/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Enqueue processing task
    background_tasks.add_task(process_event, "github", payload)

    return {"status": "ok", "message": "GitHub event received and processing started"}

@app.post("/webhooks/slack")
async def slack_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Enqueue processing task
    background_tasks.add_task(process_event, "slack", payload)

    return {"status": "ok", "message": "Slack event received and processing started"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
