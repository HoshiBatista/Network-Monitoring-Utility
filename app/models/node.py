from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NodeStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_status: Mapped[str] = mapped_column(
        String(10), nullable=False, default=NodeStatus.UNKNOWN, server_default=NodeStatus.UNKNOWN
    )
    last_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    logs: Mapped[list["StatusLog"]] = relationship(  # noqa: F821
        "StatusLog", back_populates="node", cascade="all, delete-orphan"
    )
