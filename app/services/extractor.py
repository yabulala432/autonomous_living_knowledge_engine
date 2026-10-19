from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import DECISION_EXTRACTION_SYSTEM_PROMPT, DECISION_EXTRACTION_USER_PROMPT_TEMPLATE
from app.models.schemas import DecisionExtractionResult

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def extract_decision(
    event_source: str,
    author_handle: str,
    timestamp: str,
    raw_event_content: str
) -> DecisionExtractionResult:
    """
    Uses the OpenAI Beta Structured Outputs API to parse raw events into a DecisionExtractionResult.
    """
    formatted_user_prompt = DECISION_EXTRACTION_USER_PROMPT_TEMPLATE.format(
        event_source=event_source,
        author_handle=author_handle,
        timestamp=timestamp,
        raw_event_content=raw_event_content
    )

    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": DECISION_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": formatted_user_prompt},
        ],
        response_format=DecisionExtractionResult,
    )

    decision = response.choices[0].message.parsed
    return decision
