from pydantic import BaseModel, Field
from typing import List


class PlannerConfig(BaseModel):
    """Configuration for the Planner agent."""

    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    max_retries: int = Field(default=3, le=5, description="Maximum retry attempts")
    max_history_records: int = Field(
        default=2, le=10, description="Max conversation history records to include"
    )
    temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="LLM temperature"
    )
    max_tokens: int = Field(
        default=2000, gt=0, description="Maximum tokens in LLM response"
    )


class EvaluationResult(BaseModel):
    is_sufficient: bool
    confidence_score: float
    missing_aspects: List[str]
    suggested_followups: List[str]
