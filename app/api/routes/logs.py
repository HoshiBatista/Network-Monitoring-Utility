from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.node import Node
from app.models.status_log import StatusLog
from app.schemas.status_log import StatusLogResponse

router = APIRouter(tags=["logs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/nodes/{node_id}/logs", response_model=list[StatusLogResponse])
async def get_node_logs(node_id: int, session: SessionDep):
    if not await session.get(Node, node_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
    result = await session.execute(
        select(StatusLog)
        .where(StatusLog.node_id == node_id)
        .order_by(StatusLog.timestamp.desc())
    )
    return result.scalars().all()


@router.get("/logs", response_model=list[StatusLogResponse])
async def list_all_logs(
    session: SessionDep,
    limit: int = Query(100, ge=1, le=1000),
):
    result = await session.execute(
        select(StatusLog).order_by(StatusLog.timestamp.desc()).limit(limit)
    )
    return result.scalars().all()
