import json
import os

from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import ClassificationRequest, ClassificationResponse

router = APIRouter()


@router.post("/classify", response_model=ClassificationResponse)
async def classify_intent(request: Request, body: ClassificationRequest):
    service = request.app.state.classification_service
    try:
        result = await service.classify(body.message)
        return ClassificationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/classify/reliable", response_model=ClassificationResponse)
async def classify_reliable(
    request: Request,
    body: ClassificationRequest,
    strategy_level: int = Query(default=3, ge=1, le=3),
):
    """
    strategy_level:
      1 — structured output + clean prompt
      2 — level 1 + semantic disambiguation + priority rules
      3 — level 2 + confidence thresholds + routing determinism + reliability scoring
    """
    service = getattr(request.app.state, "reliable_service", None)
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Reliable classification service unavailable (requires real_llm mode).",
        )
    try:
        result = await service.classify(body.message, strategy_level=strategy_level)
        return ClassificationResponse(
            run_id=result["run_id"],
            input=result["input"],
            predicted_intent=result["predicted_intent"],
            confidence=result["confidence"],
            intent_distribution=result["intent_distribution"],
            routing_flow=result["routing_flow"],
            generated_response=result["generated_response"],
            execution_mode=result["execution_mode"],
            timestamp=result["timestamp"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/dataset")
async def get_dataset():
    dataset_path = os.path.join(
        os.path.dirname(__file__), "../datasets/ambiguous_messages.json"
    )
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/health")
async def health(request: Request):
    cfg = request.app.state.config
    return {
        "status": "ok",
        "service": "AI Quality Engineering Lab",
        "execution_mode": cfg.execution_mode,
    }
