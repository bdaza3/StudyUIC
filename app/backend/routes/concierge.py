from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/concierge", tags=["concierge"])


class ConciergePlanRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    mode: Literal["auto", "spot_search", "group_match"] = "auto"


class ConciergePlanResponse(BaseModel):
    status: Literal["scaffold"]
    mode: Literal["spot_search", "group_match"]
    message: str
    next_stage: list[str]


def _resolve_mode(request: ConciergePlanRequest) -> Literal["spot_search", "group_match"]:
    if request.mode != "auto":
        return request.mode

    group_terms = ("host", "meetup", "study group", "study block", "with others")
    if any(term in request.message.lower() for term in group_terms):
        return "group_match"
    return "spot_search"


@router.post("/plan", response_model=ConciergePlanResponse)
async def create_concierge_plan(request: ConciergePlanRequest) -> ConciergePlanResponse:
    """Validate concierge intent before the AI orchestration layer is connected."""
    mode = _resolve_mode(request)
    next_stage = [
        "Add a LangGraph planner for structured intent extraction",
        "Connect semantic spot retrieval through Supabase pgvector",
    ]
    if mode == "group_match":
        next_stage.append("Add calendar-aware conflict resolution and beacon creation")
    else:
        next_stage.append("Rank live activity and spot constraints")

    return ConciergePlanResponse(
        status="scaffold",
        mode=mode,
        message=request.message,
        next_stage=next_stage,
    )