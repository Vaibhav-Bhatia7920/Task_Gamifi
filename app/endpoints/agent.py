from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.harness import run_agent, run_pipeline
from app.config import OPENAI_API_KEY
from app.db.orm import Timeline, User, create_timeline, get_db, get_timeline, list_timelines
from app.endpoints.auth import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)


class IngestRequest(BaseModel):
    raw_data: Optional[str] = None
    topic: Optional[str] = None


class TimelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    title: str
    category: str
    source: str
    raw_data: str
    structured: Dict[str, Any]
    timeline_plan: Dict[str, Any]
    rewards: Dict[str, Any]
    compiled: Dict[str, Any]
    total_points: int
    approved: bool


def _require_openai_key() -> None:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not set in app/.env",
        )


async def _persist_pipeline(db: AsyncSession, result: Dict[str, Any], user: User) -> Timeline:
    compiled = result.get("compiled") or {}
    structured = result.get("structured") or {}
    return await create_timeline(
        db,
        user_id=user.id,
        title=compiled.get("title") or structured.get("title") or "Untitled timeline",
        category=compiled.get("category") or structured.get("category") or "",
        source=result.get("source") or "system",
        raw_data=result.get("raw_data") or "",
        structured=structured,
        timeline_plan=result.get("timeline") or {},
        rewards=result.get("rewards") or {},
        compiled=compiled,
        total_points=int(compiled.get("total_points") or 0),
        approved=bool(compiled.get("approved", True)),
    )


@router.post("/ingest", response_model=TimelineOut, status_code=status.HTTP_201_CREATED)
async def ingest(
    payload: IngestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Timeline:
    _require_openai_key()
    try:
        result = await run_pipeline(raw_data=payload.raw_data, topic=payload.topic)
        return await _persist_pipeline(db, result, user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/run", response_model=TimelineOut, status_code=status.HTTP_201_CREATED)
async def run(
    payload: AgentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Timeline:
    _require_openai_key()
    try:
        result = await run_agent(payload.message)
        return await _persist_pipeline(db, result, user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/timelines", response_model=List[TimelineOut])
async def timelines(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[Timeline]:
    return await list_timelines(db, user.id)


@router.get("/timelines/{timeline_id}", response_model=TimelineOut)
async def timeline_detail(
    timeline_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Timeline:
    row = await get_timeline(db, timeline_id, user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline not found")
    return row
