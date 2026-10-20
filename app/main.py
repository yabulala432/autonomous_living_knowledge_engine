import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from typing import Dict, Any

from app.database.connection import db, get_db_pool
from app.services.extractor import extract_decision
from app.services.embeddings import generate_embedding
from app.services.retrieval import find_relevant_documents
from app.services.evaluator import evaluate_drift
from app.services.github import create_doc_fix_pr
from app.services.synthesis import generate_sprint_digest
from app.services.telegram import send_telegram_alert

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
    elif event_source == "telegram":
        message = payload.get("message") or payload.get("channel_post") or {}
        source_id = str(message.get("message_id", "unknown_msg"))
        from_user = message.get("from") or {}
        author = from_user.get("username") or from_user.get("first_name", "unknown_user")
        raw_content = message.get("text") or message.get("caption", "")

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

            decision_id = await conn.fetchval(
                """
                INSERT INTO decisions (workspace_id, event_id, title, rationale, impacted_scope, embedding)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                workspace_id, event_id, decision.title, decision.rationale, decision.impacted_systems, embedding
            )

            # --- Milestone 3 Pipeline ---
            print(f"Decision logged. ID: {decision_id}. Scanning for drift...")

            # 4. Retrieve candidate documents
            relevant_docs = await find_relevant_documents(embedding, workspace_id)
            print(f"Found {len(relevant_docs)} candidate documents for review.")

            for doc in relevant_docs:
                # 5. Evaluate drift
                evaluation = await evaluate_drift(decision, doc)

                # 6. Trigger action if drift detected
                if evaluation.has_drift:
                    print(f"🚨 DRIFT DETECTED in {doc['file_path']} (Severity: {evaluation.severity})")
                    pr_url = await create_doc_fix_pr(workspace_id, str(decision_id), doc, evaluation)

                    # Send notification to Telegram
                    alert_text = (
                        f"🚨 *Documentation Drift Detected!*\n\n"
                        f"📄 *File:* `{doc['file_path']}`\n"
                        f"⚠️ *Severity:* {evaluation.severity.upper()}\n"
                        f"💡 *Decision:* {decision.title}\n\n"
                        f"📝 *Analysis:*\n{evaluation.drift_analysis}\n\n"
                        f"🔗 [Review Pull Request]({pr_url})"
                    )
                    await send_telegram_alert(alert_text)
                else:
                    print(f"✅ No drift in {doc['file_path']}")


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

@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Enqueue processing task
    background_tasks.add_task(process_event, "telegram", payload)

    return {"status": "ok", "message": "Telegram event received and processing started"}

@app.get("/reports/sprint")
async def get_sprint_digest(days: int = 7):
    # Mocking workspace_id for the MVP
    workspace_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    report = await generate_sprint_digest(workspace_id, days_back=days)
    return {"report": report}

@app.post("/reports/sprint/telegram")
async def send_sprint_digest_to_telegram(days: int = 7):
    workspace_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    report = await generate_sprint_digest(workspace_id, days_back=days)
    msg = f"📊 *Executive Sprint Digest (Past {days} Days)*\n\n{report}"
    success = await send_telegram_alert(msg)
    return {"sent_to_telegram": success, "report": report}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
