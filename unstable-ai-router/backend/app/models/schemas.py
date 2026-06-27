from typing import Dict

from pydantic import BaseModel, Field


class ClassificationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ClassificationResponse(BaseModel):
    run_id: str
    input: str
    predicted_intent: str
    confidence: float
    intent_distribution: Dict[str, float]
    routing_flow: str
    generated_response: str
    execution_mode: str
    timestamp: str
