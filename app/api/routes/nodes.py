from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.node import Node
from app.schemas.node import NodeCreate, NodeResponse, NodeUpdate

router = APIRouter(prefix="/nodes", tags=["nodes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[NodeResponse])
async def list_nodes(session: SessionDep):
    result = await session.execute(select(Node).order_by(Node.id))
    return result.scalars().all()


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(payload: NodeCreate, session: SessionDep):
    existing = await session.execute(select(Node).where(Node.address == payload.address))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node with this address already exists.",
        )
    node = Node(address=payload.address, port=payload.port)
    session.add(node)
    await session.commit()
    await session.refresh(node)
    logger.info(f"Created node {node.id}: {node.address}")
    return node


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, session: SessionDep):
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(node_id: int, payload: NodeUpdate, session: SessionDep):
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(node, field, value)
    await session.commit()
    await session.refresh(node)
    logger.info(f"Updated node {node_id}")
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: int, session: SessionDep):
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
    await session.delete(node)
    await session.commit()
    logger.warning(f"Deleted node {node_id}: {node.address}")
