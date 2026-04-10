from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.node import Node
from app.schemas.node import NodeCreate, NodeResponse, NodeUpdate

router = APIRouter(prefix="/nodes", tags=["nodes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[NodeResponse])
async def list_nodes(session: SessionDep) -> list[Node]:
    result = await session.execute(select(Node).order_by(Node.id))
    return list(result.scalars().all())


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(payload: NodeCreate, session: SessionDep) -> Node:
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
    logger.info("Created node {}: {}", node.id, node.address)
    return node


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, session: SessionDep) -> Node:
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(node_id: int, payload: NodeUpdate, session: SessionDep) -> Node:
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")

    updates = payload.model_dump(exclude_unset=True)

    # Check for address conflict before committing to avoid an unhandled IntegrityError.
    new_address = updates.get("address")
    if new_address and new_address != node.address:
        conflict = await session.execute(select(Node).where(Node.address == new_address))
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A node with this address already exists.",
            )

    for field, value in updates.items():
        setattr(node, field, value)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A node with this address already exists.",
        )

    await session.refresh(node)
    logger.info("Updated node {}", node_id)
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: int, session: SessionDep) -> None:
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
    await session.delete(node)
    await session.commit()
    logger.warning("Deleted node {}: {}", node_id, node.address)
