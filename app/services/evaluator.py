from typing import Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import DRIFT_EVALUATION_SYSTEM_PROMPT, DRIFT_EVALUATION_USER_PROMPT_TEMPLATE
from app.models.schemas import DecisionExtractionResult, DriftEvaluationResult

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def evaluate_drift(decision: DecisionExtractionResult, document: Dict[str, Any]) -> DriftEvaluationResult:
    """
    Evaluates a new technical decision against an existing document to detect documentation drift.
    Returns a DriftEvaluationResult which includes patched markdown if drift is detected.
    """
    formatted_user_prompt = DRIFT_EVALUATION_USER_PROMPT_TEMPLATE.format(
        decision_title=decision.title,
        decision_summary=decision.summary,
        decision_rationale=decision.rationale,
        decision_impacted_systems=", ".join(decision.impacted_systems),
        decision_breaking_changes=", ".join(decision.breaking_changes),
        document_file_path=document["file_path"],
        document_repo_name=document["repo_name"],
        document_content=document["content"]
    )

    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": DRIFT_EVALUATION_SYSTEM_PROMPT},
            {"role": "user", "content": formatted_user_prompt},
        ],
        response_format=DriftEvaluationResult,
    )

    evaluation = response.choices[0].message.parsed
    return evaluation
