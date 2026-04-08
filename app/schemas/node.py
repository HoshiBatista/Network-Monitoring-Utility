from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.node import NodeStatus


class NodeCreate(BaseModel):
    address: str = Field(..., min_length=1, max_length=255, description="IP address or hostname")
    port: Optional[int] = Field(None, ge=1, le=65535, description="TCP port to probe (optional)")


class NodeUpdate(BaseModel):
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)


class NodeResponse(BaseModel):
    id: int
    address: str
    port: Optional[int]
    last_status: NodeStatus
    last_latency: Optional[float]
    last_check_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
