from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.status_log import StatusLog


class NodeStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_status: Mapped[str] = mapped_column(
        String(10), nullable=False, default=NodeStatus.UNKNOWN.value
    )
    last_latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    logs: Mapped[list[StatusLog]] = relationship(
        "StatusLog", back_populates="node", cascade="all, delete-orphan"
    )
