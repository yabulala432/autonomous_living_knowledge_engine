from typing import List, Literal
from pydantic import BaseModel, Field

# --- Schema 1: Decision Extractor ---
class DecisionExtractionResult(BaseModel):
    is_architectural_decision: bool = Field(
        ..., description="True if the event represents a notable technical decision or policy."
    )
    title: str = Field(..., max_length=120)
    summary: str
    rationale: str
    impacted_systems: List[str]
    breaking_changes: List[str]
    stakeholders: List[str]
    search_queries: List[str]

# --- Schema 2: Drift Evaluator ---
class DriftEvaluationResult(BaseModel):
    has_drift: bool
    severity: Literal["none", "low", "medium", "critical"]
    drift_analysis: str
    exact_conflicting_excerpt: str
    pull_request_title: str
    pull_request_body: str
    updated_full_document: str
