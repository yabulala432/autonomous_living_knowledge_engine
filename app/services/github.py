from typing import Dict, Any
import uuid
from app.models.schemas import DriftEvaluationResult
from app.database.connection import get_db_pool

async def create_doc_fix_pr(
    workspace_id: uuid.UUID,
    decision_id: str,
    document: Dict[str, Any],
    evaluation: DriftEvaluationResult
) -> str:
    """
    Mocks opening a GitHub PR to fix documentation drift.
    Records the attempt in the drift_tickets table.
    """

    # 1. Log the action (Mocking the PyGithub or httpx API calls)
    print("="*50)
    print(f"🚀 ACTION DISPATCHER: Opening GitHub PR for {document['repo_name']}")
    print(f"Branch: chore/docs-sync-{decision_id[:8]}")
    print(f"Title: {evaluation.pull_request_title}")
    print(f"Body: \n{evaluation.pull_request_body}")
    print(f"File to update: {document['file_path']}")
    print("="*50)

    mock_pr_url = f"https://github.com/{document['repo_name']}/pull/{uuid.uuid4().hex[:4]}"

    # 2. Record the drift ticket in the database
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO drift_tickets
            (workspace_id, decision_id, document_id, conflict_explanation, proposed_diff, github_pr_url, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            workspace_id,
            uuid.UUID(decision_id),
            uuid.UUID(document["id"]),
            evaluation.drift_analysis,
            evaluation.updated_full_document,
            mock_pr_url,
            "pr_created"
        )

    return mock_pr_url
